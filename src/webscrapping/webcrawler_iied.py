from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIIED(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://pubs.iied.org"
        self.start_page = 0

    def prepare_query(self, query, page):
        if re.search("&page=\d+", query) == None:
            return query + "&page=%d"%(page)
        return re.sub("&page=\d+", "&page=%d"%(page), query)

    def extract_links(self, doc):
        return [item['onclick'].split("'")[1] for item in doc.findAll(class_='node node--type-publication node--view-mode-search-result ds-1col clearfix')]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split('/')[-1]
        self.fetch(
            article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def get_published_year(self, meta_doc):
        year = ""
        for li_tag in meta_doc.select(".info_blkkv_in li"):
            if "published" in li_tag.select("span")[0].text.lower():
                year_group = re.search("\d{4}",li_tag.text)
                if year_group != None:
                    return year_group.group(0)
        return year

    def get_keywords(self, meta_doc):
        keywords = []
        for li_tag in meta_doc.select(".info_blkkv_in li"):
            if "theme" in li_tag.select("span")[0].text.lower() or "area" in li_tag.select("span")[0].text.lower():
                keywords.extend([a_tag.text for a_tag in li_tag.select("a")])
        return ";".join(keywords)

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "IIED"
        df["title"].values[i] = meta_doc.select(".publication__node-title > h1")[0].text.strip()
        if len(meta_doc.select(".mb-3 ul")) > 0:
            df["authors"].values[i] = meta_doc.select(".mb-3 ul")[0].get_text(separator=u';')
        df["abstract"].values[i] = meta_doc.select(".publication__body")[0].get_text(separator=u';')
        return df
