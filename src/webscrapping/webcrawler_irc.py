from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIRC(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.ircwash.org"
        self.start_page = 0
        self.article_id_2_url = {}

    def prepare_query(self, query, page):
        if re.search("page=\d+", query) == None:
            return query + "&page=%d"%(page)
        return re.sub("page=\d+", "page=%d"%(page), query)

    def extract_links(self, doc):
        return  [ item['href'] for item in doc.select('a') if item.text.lower().strip() == "biblio info"] 

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split("/")[-1]
        self.article_id_2_url[f'{article_id}.html'] = article_url
        self.fetch(
            article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def fill_df_fields(self, doc, df, i):
        df["source_name"].values[i] = "IRC"
        mapping = {
            "title": "title",
            "year of publication": "year",
            "authors": "authors",
            "abstract": "abstract",
            "keywords": "keywords",
            "publisher": "publisher"
        }
        for obj in doc.select("td.biblio-row-title"):
            table_row_name = obj.text.lower().strip()
            table_row_value = obj.findNextSibling().text.strip()
            if table_row_name in mapping:
                if table_row_name == "authors" and len(obj.findNextSibling().select("a")):
                    authors = []
                    for obj in obj.findNextSibling().select("a"):
                        authors.append(obj.text.strip().replace(",", ""))
                    df["authors"].values[i] = ";".join(authors)
                elif table_row_name == "keywords":
                    df[mapping[table_row_name]].values[i] = table_row_value.replace(",", ";")
                else:
                    df[mapping[table_row_name]].values[i] = table_row_value

        df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
        downloads_part = None
        for obj in doc.select("h2.headline"):
            if "downloads" in obj.text.lower():
                downloads_part = obj.parent.parent
        if downloads_part is not None and len(downloads_part.select("a")):
            df["url"].values[i] = downloads_part.select("a")[0]["href"]
        else:
            df["url"].values[i] = self.article_id_2_url[df["article_name"].values[i]]
        return df