from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerSanitationAll(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.sanitationandwaterforall.org"
        self.start_page = 0
        self.article_id_2_url = {}

    def prepare_query(self, query, page):
        if re.search("page=\d+", query) == None:
            return query + "&page=%d"%(page)
        return re.sub("page=\d+", "page=%d"%(page), query)

    def extract_links(self, doc):
        return  [ item['href'] for item in doc.select('a.read-more')] 

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split("/")[-1]
        self.article_id_2_url[f'{article_id}.html'] = self.domain_name + article_url
        self.fetch(
            self.domain_name + article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def fill_df_fields(self, doc, df, i):
        df["source_name"].values[i] = "sanitationandwaterforall"
        df["title"].values[i] = " ".join(w.text for w in doc.select("h1 span")).strip()
        if len(doc.select("div.tool__field-year-publication div.field__item")):
            df["year"].values[i] = doc.select("div.tool__field-year-publication div.field__item")[0].text
        abstract = ""
        if len(doc.select("div.tool__field-target-audience")):
            abstract = abstract + "\n" + doc.select("div.tool__field-target-audience")[0].text.strip()
        if len(doc.select("div.tool__body")):
            abstract = abstract + "\n" + doc.select("div.tool__body")[0].text.strip()
        df["abstract"].values[i] = abstract.strip()
        df["keywords"].values[i] = ";".join(
            [w.text.strip() for w in doc.select("div.tool__field-type div.field__items div.field__item")])
        df["affiliation"].values[i] = ";".join(
            [w.text.strip() for w in doc.select("div.tool__field-organization div.field__items div.field__item")])

        df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
        df["url"].values[i] = self.article_id_2_url[df["article_name"].values[i]]
        return df