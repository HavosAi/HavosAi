from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerDFID(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.gov.uk"

    def prepare_query(self, query, page):
        if re.search("&page=\d+", query) == None:
            return query + "&page=%d"%(page)
        return re.sub("&page=\d+", "&page=%d"%(page), query)

    def extract_links(self, doc):
        return [item['href'] for item in doc.select('li.gem-c-document-list__item a')]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split('/')[-1][:100]
        self.fetch(
            self.domain_name + article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def get_url_from_page(self, meta_doc):
        if len(meta_doc.select("#links")) > 0:
            if meta_doc.select("#links")[0].find_next_sibling("p") != None:
                return meta_doc.select("#links")[0].find_next_sibling("p").select("a")[0]["href"]
            elif meta_doc.select("#links")[0].find_next_sibling("ul") != None:
                if len(meta_doc.select("#links")[0].find_next_sibling("ul").select("a")) > 0:
                    return meta_doc.select("#links")[0].find_next_sibling("ul").select("a")[0]["href"]
                else:
                    return meta_doc.select("#links")[0].find_next_sibling("ul").select("li")[0].text.split("(")[1][:-1]
        elif len(meta_doc.select("#link")) > 0:
            return meta_doc.select("#link")[0].find_next_sibling("p").select("a")[0]["href"]
        return ""

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "DFID"
        df["title"].values[i] = meta_doc.select(".gem-c-title__text")[0].text.strip()
        df["year"].values[i] = self.extract_year(meta_doc.select(".app-c-published-dates")[0].text.strip(), df["year"].values[i])
        if len(meta_doc.select("#details")) > 0:
            df["abstract"].values[i] = meta_doc.select("#details")[0].get_text(separator=u' ')
        df["url"].values[i] = self.get_url_from_page(meta_doc)
        return df