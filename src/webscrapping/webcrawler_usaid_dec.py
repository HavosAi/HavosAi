from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os
import requests
import json
import pickle
import time
import pandas as pd
from selenium import webdriver
from webscrapping import webcrawler_logger
from utilities import excel_writer

class WebCrawlerUsaidDec(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://dec.usaid.gov"
        self.delay = 3
        self.use_selenium = True

    def extract_links(self, doc):
        return [item['href'] for item in doc.findAll(class_="f") if item.text == 'More Details']

    def process_all_links(self, articles, folder_to_save, query):
        processed_links = []
        try:
            driver = webdriver.Chrome(executable_path=self.SELENIUM_DRIVER_PATH, chrome_options=self.chromeOptions)
            for ind, article in enumerate(articles):
                try:
                    if article in processed_links:
                        continue
                    article_id = '_'.join(article.split('&')[-1])
                    file_path = os.path.join(folder_to_save, f'{article_id}.html')

                    driver.get(article)
                    print(f'Waiting time for loading: {self.delay} seconds for {article}')
                    time.sleep(self.delay)
                    html = driver.page_source

                    print("Url was searched")
                    if file_path is not None:
                        print(file_path)
                        with open(file_path, 'w') as file:
                            file.write(html)
                        print("Saved.")

                    processed_links.append(article)
                    self.sleep(1)
                except:
                    print("(Selenium) The problem with url %s" % article)
                    try:
                        self._webcrawler_logger.update_status_for_query(article, "Finished with errors",
                                                                        "The problem with url %s" % article)
                    except:
                        pass
                if ind > 0 and ind % 5 == 0:
                    self._webcrawler_logger.update_webscrapping_results(query, articles[ind-5:ind], 5)
            driver.close()
        except:
            print("Error with chrome driver load.")

        return processed_links, len(articles) if len(processed_links) > 0 else 0

    def extract_all_links(self, query):
        all_pages = []
        if len(self.check_url(query)) == 0:
            try:
                driver = webdriver.Chrome(executable_path=self.SELENIUM_DRIVER_PATH, chrome_options=self.chromeOptions)
                driver.get(query)
                while True:
                    print(f'Waiting time for loading: {self.delay} seconds')
                    time.sleep(self.delay)
                    doc = driver.page_source
                    articles = self.extract_links(self.parse(doc))
                    print(articles)
                    all_pages += articles

                    buttons = driver.find_elements_by_xpath("//*[text() = 'Next']")
                    if len(buttons) == 0:
                        break
                    else:
                        driver.execute_script("arguments[0].click();", buttons[0])

                    # self._webcrawler_logger.update_webscrapping_results(query, processed_links, articles_in_page)
                driver.close()
                print('All links were extracted')
            except:
                print('Problems with selenium.')
        else:
            self._webcrawler_logger.update_status_for_query(query, "Finished with errors", self.check_url(query))
        return all_pages

    def crawl_query(self, query, folder_to_save, start_page=None, log_status_filename=""):

        if not os.path.exists(folder_to_save):
            os.makedirs(folder_to_save)
        self._webcrawler_logger = webcrawler_logger.WebcrawlerLogger(log_status_filename)

        all_links = self.extract_all_links(query)
        self.process_all_links(all_links, folder_to_save, query)

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "USAID DEC"
        table = meta_doc.findAll('center')[0].findAll('table')
        table_df = pd.read_html(str(table))[0]
        mapping = {'Title': 'title',
                   'Author': 'authors',
                   'Abstract': 'abstract',
                   'Date': 'year',
                   'Publisher': 'publisher',
                   'Term': 'keywords',
                   'URI': 'url'}
        for row in table_df.iterrows():
            key, value = row[1][0], row[1][1]
            for k, v in mapping.items():
                if type(key) == str and k in key:
                    df[v].values[i] = str(value).strip()
        df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
        return df
