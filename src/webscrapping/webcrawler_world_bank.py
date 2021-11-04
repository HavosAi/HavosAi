from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerWorldBank(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://openknowledge.worldbank.org"

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("page=\d+", "page=%d"%(page), query)

	def extract_links(self, doc):
	    return  [ item['href'] for item in doc.select('div > h4 > a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.fetch(
	        self.domain_name + article_url + '?show=full',
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def parse_metadata_tags(self, meta_doc, tag_name):
		return ";".join([tag['content'] for tag in meta_doc.findAll(attrs={"name" : tag_name})])

	def parse_journal_name(self, meta_doc):
	    relations =  meta_doc.findAll(attrs={"name":"DC.relation"})
	    for relation in relations:
	        if not "CC BY" in relation['content'] and not "http" in relation['content']:
	            return relation['content'].split('No.')[0].replace(";", "")
	    return ""

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "WorldBank"
	    df["authors"].values[i] = self.parse_metadata_tags(meta_doc, "DC.creator")
	    df["year"].values[i] = self.extract_year(self.parse_metadata_tags(meta_doc, "DCTERMS.issued"), df["year"].values[i])
	    df["abstract"].values[i] = self.parse_metadata_tags(meta_doc, "DCTERMS.abstract")
	    df["publisher"].values[i] = self.parse_metadata_tags(meta_doc, "DC.publisher")
	    df["title"].values[i] = self.parse_metadata_tags(meta_doc, "DC.title")
	    df["url"].values[i] = self.parse_metadata_tags(meta_doc, "citation_abstract_html_url")
	    df["keywords"].values[i] = self.parse_metadata_tags(meta_doc, "citation_keywords")
	    df["journal_name"].values[i] = self.parse_journal_name(meta_doc)
	    return df