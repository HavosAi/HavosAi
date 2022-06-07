from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os
from selenium import webdriver

class WebCrawlerIFPRI(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "http://ebrary.ifpri.org"
        self.use_selenium = True

    def prepare_query(self, query, page):
        if re.search("/page/\d+", query) == None:
            return query + "/page/%d"%page
        return re.sub("/page/\d+", "/page/%d"%(page), query)

    def extract_links(self, doc):
        return [item['href'] for item in doc.findAll(class_="SearchResult-container shared-search-box shared-box row SearchResult cdm-item-card null")]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = '_'.join(article_url.split('/')[-6:])
        self.fetch(
            self.domain_name + article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def join_spans(self, meta_doc):
        return ";".join([item.text for item in meta_doc.findAll("span")]).strip()

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "IFPRI"
        meta_doc = meta_doc.find(class_="ItemView-itemMetadata item-description ItemMetadata-itemMetaPrint table")
        df["title"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-title").find(class_="field-value").text
        df["authors"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-creato").find(class_="field-value").get_text(separator=u';')
        df["year"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-date").find(class_="field-value").text
        df["keywords"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-loc").find(class_="field-value").get_text(separator=u';')
        df["fulltext_links"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-full").find(class_="field-value").find('a')['href']
        df["abstract"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-descri").find(class_="field-value").text
        df["publisher"].values[i] = meta_doc.find(class_="ItemMetadata-metadatarow field-publis").find(class_="field-value").text
        return df
