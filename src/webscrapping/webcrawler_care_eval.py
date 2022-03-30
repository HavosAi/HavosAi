from webscrapping.webcrawler_base import WebCrawlerBase
from pathlib import Path
import re
import os


class WebCrawlerCareEval(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "http://careevaluations.org"

    def prepare_query(self, query, page):
        query, params = query.split("?")
        if re.search("page/\d+", query) == None:
            return query + "page/%d" % (page) + '?' + params
        return re.sub("page/\d+", "page/%d" % (page), query) + '?' + params

    def extract_links(self, doc):
        return [item['href'] for item in doc.select('h2 > a')]

    def extract_articles(self, doc):
        return doc.findAll(attrs={"class": "fl-post-text"})

    def process_article(self, article, folder_to_save):
        article_url = self.extract_links(article)[0]
        article_id = article_url.split('/')[-2]
        file_path = os.path.join(folder_to_save, f'{article_id[:50]}.html')

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
        df["source_name"].values[i] = "Care Evaluations"
        df["title"].values[i] = meta_doc.find("h2").text.strip()
        df["abstract"].values[i] = meta_doc.find(class_="fl-post-excerpt").text.strip()
        doc_post_data = meta_doc.find(class_="fl-post-meta")
        for li in doc_post_data.findAll('li'):
            key, value = li.text.split(':')
            if key == "Publication Date":
                df["year"].values[i] = self.extract_year(value, df["year"].values[i])
            if key == "Keywords":
                df["keywords"].values[i] = value
        df["fulltext_links"].values[i] = self.extract_links(meta_doc)[0]
        return df
