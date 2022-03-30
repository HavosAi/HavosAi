from webscrapping.webcrawler_base import WebCrawlerBase
from pathlib import Path
import re
import os


class WebCrawlerGoogleScholar(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://scholar.google.com"
        self.start_page = 0

    def prepare_query(self, query, page):
        if re.search("start=\d+", query) == None:
            return query + "&start=%d" % (page*10)
        return re.sub("start=\d+", "page=%d" % (page*10), query)

    def extract_links(self, doc):
        return [item['href'] for item in doc.select('h3 > a')]

    def extract_articles(self, doc):
        return doc.findAll(attrs={"class": "gs_ri"})

    def extract_id(self, doc):
        return [item['id'] for item in doc.select('h3 > a')]

    def process_article(self, article, folder_to_save):
        article_id = self.extract_id(article)[0]
        file_path = os.path.join(folder_to_save, f'{article_id}.html')

        if file_path is not None:
            print(f'Save {article_id} to {file_path}')
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
            article_id = self.extract_id(article)[0]
            if article_id in added_ids_from_previous_page:
                continue
            self.process_article(article, folder_to_save)
            added_ids_from_previous_page.add(article_id)
            processed_links.append(article_id)

        return processed_links, len(articles) if len(processed_links) > 0 else 0, added_ids_from_previous_page

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "Google Scholar"
        df["abstract"].values[i] = meta_doc.find(class_="gs_rs").get_text().strip()
        df["title"].values[i] = meta_doc.find(class_='gs_rt').get_text().strip()
        df["year"].values[i] = self.extract_year(meta_doc.find(class_="gs_a").get_text().strip(),
                                                 df["year"].values[i])
        df["authors"].values[i] = meta_doc.find(class_="gs_a").get_text().strip()
        df["fulltext_links"].values[i] = self.extract_links(meta_doc)[0]
        return df
