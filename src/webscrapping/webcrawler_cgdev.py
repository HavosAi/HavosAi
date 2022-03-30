from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCGDev(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.cgdev.org"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d" % (page)
		return re.sub("page=\d+", "page=%d" % (page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('div.search-result-left a') if 'publication' in item['href']]

	def process_article(self, article_url, folder_to_save):
		print(article_url)
		article_id = article_url.split('/')[-1]
		self.fetch(
			self.domain_name + article_url,
			os.path.join(folder_to_save, f'{article_id}.html')
		)

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "CGDev"
		df["title"].values[i] = meta_doc.find("h1").text.strip()
		df["abstract"].values[i] = meta_doc.find(class_="field-body-blog-post w3-bar-item field__item").text.strip()
		df["year"].values[i] = self.extract_year(meta_doc.find(class_="published-time").text.strip(),
												 df["year"].values[i])
		df["authors"].values[i] = ";".join([w.text.strip()
											for w in meta_doc.find(class_="w3-clear w3-section field field--name-field-authors field--type-entity-reference field--label-hidden field__items").findAll(class_="w3-bar-item field__item")])
		df["fulltext_links"].values[i] = meta_doc.select("div.page-title a")[0]['href']
		return df
		