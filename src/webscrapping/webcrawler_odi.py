from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerODI(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.odi.org"
        self.start_page = 1

    def prepare_query(self, query, page):
        if re.search("page=\d+", query) == None:
            return query + "&page=%d"%(page)
        return re.sub("page=\d+", "page=%d"%(page), query)

    def extract_links(self, doc):
        return [item['href'] for item in doc.select('h3 > a')]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split('/')[-2]
        self.fetch(
            self.domain_name + article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def get_tag_text(self, meta_doc, tag):
        res = meta_doc.select(tag)
        if len(res) > 0:
            return res[0].text.replace("\xa0","").replace("\n"," ")
        return ""

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "ODI"
        df["title"].values[i] = self.get_tag_text(meta_doc,"h1.header__title")
        df["year"].values[i] = self.extract_year(self.get_tag_text(meta_doc,"div.field--name-field-start-date"), df["year"].values[i])
        df["authors"].values[i] = ";".join(self.get_tag_text(meta_doc,"div.field--name-field-people").replace(" and "," , ").split(","))
        abstract_text = self.get_tag_text(meta_doc, "div.field--name-field-paragraph-body")
        abstract_text = abstract_text + " " + self.get_tag_text(meta_doc, "div.field--type-text-with-summary")
        df["abstract"].values[i] = abstract_text + " " + " ".join(["" if len(tag.select("a")) > 0 else tag.text.replace("\xa0","").replace("\n"," ") for tag in meta_doc.select("p")])
        df["keywords"].values[i] = ";".join([tag.text for tag in meta_doc.select("div.related-themes > ul > li")])
        urls = meta_doc.select("div.field--name-field-document-file div.main-title > a")
        return df
