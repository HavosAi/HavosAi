from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerDEval(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.deval.org/"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d" % (page)
		return re.sub("page=\d+", "page=%d" % (page), query)
 
	def extract_links(self, doc):
		return [item.find('a')['href'] for item in doc.findAll(class_="views-field views-field-title")]

	def process_article(self, article_url, folder_to_save):
		print(article_url)
		article_id = article_url.split('/')[-1]
		self.fetch(
			self.domain_name + article_url,
			os.path.join(folder_to_save, f'{article_id}.html')
		)

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "USAID Learning Lab"
		df["title"].values[i] = meta_doc.find("h1").text.strip()
		df["abstract"].values[i] = meta_doc.find(class_="views-field views-field-body").text.strip()
		df["year"].values[i] = self.extract_year(meta_doc.find(class_="views-field views-field-field-document-status").text.strip(), df["year"].values[i])
		df["fulltext_links"].values[i] = meta_doc.find(class_="file-link").find('a')['href']
		return df
		