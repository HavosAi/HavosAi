from webscrapping.webcrawler_base import WebCrawlerBase
from pathlib import Path
import re
import os


class WebCrawlerWorldBankIEG(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://ieg.worldbankgroup.org"
        self.start_page = 0

    def prepare_query(self, query, page):
        if re.search("page=\d+", query) == None:
            return query + "&page=%d" % (page)
        return re.sub("page=\d+", "page=%d" % (page), query)

    def extract_links(self, doc):
        return [item['href'] for item in doc.select('h3 > a')]

    def extract_articles(self, doc):
        return doc.findAll(attrs={"class": "post views-row"})

    def process_article(self, article, folder_to_save):
        article_url = self.extract_links(article)[0]
        article_id = article_url.split('/')[-1]
        file_path = os.path.join(folder_to_save, f'{article_id}.html')

        if file_path is not None:
            print(f'Save {article_url} to {file_path}')
            if Path(file_path).exists():
                print('Already exists. Skipped.')
                return

        if file_path is not None:
            with open(file_path, 'w', encoding="utf-8") as file:
                file.write(str(article))
        print("Article was saved.")

    def process_page(self, page, query, folder_to_save, added_ids_from_previous_page):
        print(f'\n\nPage {page}')

        doc = self.parse(self.fetch(
            self.prepare_query(query, page), custom_headers=self.headers
        ))

        articles = self.extract_links(doc)
        print(f"Articles: {articles}")
        processed_links = []

        for article in self.extract_articles(doc):
            article_link = self.extract_links(article)[0]
            if article_link in added_ids_from_previous_page:
                continue
            self.process_article(article, folder_to_save)
            added_ids_from_previous_page.add(article_link)
            processed_links.append(article_link)

        return processed_links, len(articles) if len(processed_links) > 0 else 0, added_ids_from_previous_page

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "WorldBankIEG"
        df["year"].values[i] = self.extract_year(meta_doc.find(attrs={"class": "date"}).get_text().strip(),
                                                 df["year"].values[i])
        df["abstract"].values[i] = meta_doc.find(attrs={"class": "fullcontent"}).get_text().strip()
        df["title"].values[i] = meta_doc.find('h3').get_text().strip()
        df["url"].values[i] = self.domain_name + "/" + self.extract_links(meta_doc)[0] + '?show=full'
        df["fulltext_links"].values[i] = self.domain_name + "/" + self.extract_links(meta_doc)[0] + '?show=full'
        return df
