from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerRWSN(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.rural-water-supply.net"
        self.start_page = 1
        self.article_id_2_url = {}

    def prepare_query(self, query, page):
        if re.search("page/\d+", query) == None:
            return query + "/page/%d"%(page)
        return re.sub("page/\d+", "page/%d"%(page), query)

    def extract_links(self, doc):
        return  [ item['href'] for item in doc.select('div.row h4.ugp30 a')] 

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split("/")[-1]
        self.article_id_2_url[f'{article_id}.html'] = self.domain_name + article_url
        self.fetch(
            self.domain_name + article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def get_title(self, doc):
        text = ""
        for w in doc.select("h2.ccbk_title"):
            for t in w.find_all(text=True, recursive = False):
                text = text + "\n" + t.strip()
        return text.strip()

    def get_abstract(self, doc):
        abstract = ""
        started = False
        for w in doc.select("h2.ccbk_title"):
            for tag in w.parent.children:
                if tag.name == "p":
                    if "description" in tag.text.lower() or "abstract" in tag.text.lower():
                        started = True
                    elif started:
                        abstract = abstract + "\n" + tag.text.strip()
                elif tag.name is not None:
                    started = False
        return abstract.strip()

    def get_url_to_download(self, doc):
        for w in doc.select("form input"):
            if w["name"] == "file":
                return self.domain_name + "/" + w["value"]
        return ""
    
    def fill_df_fields(self, doc, df, i):
        df["source_name"].values[i] = "RWSN"
        df["title"].values[i] = self.get_title(doc)
        df["abstract"].values[i] = self.get_abstract(doc)
        df["url"].values[i] = self.get_url_to_download(doc)
        if not df["url"].values[i]:
            df["url"].values[i] = self.article_id_2_url[df["article_name"].values[i]]
        mapping = {
            "year of publishing": "year",
            "author": "authors",
            "publisher": "publisher",
            "institution": "affiliation"
        }
        for w in doc.select("p.ugp30")[0].parent:
            if w.name == "p" and w.b is not None:
                column_name = w.b.text.strip().lower()
                text = ""
                for t in w.b.parent.find_all(text=True, recursive = False):
                    text = text + "\n" + t.strip()
                text = text.strip()
                if column_name in mapping:
                    df[mapping[column_name]].values[i] = text

        df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
        return df