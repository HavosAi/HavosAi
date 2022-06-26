from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIADB(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://publications.iadb.org"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d" % (page)
		return re.sub("page=\d+", "page=%d" % (page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('span.field-content a')]

	def process_article(self, article_url, folder_to_save):
		print(article_url)
		article_id = article_url.split('/')[-1]
		self.fetch(
			self.domain_name + article_url,
			os.path.join(folder_to_save, f'{article_id}.html')
		)

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "IADB"
		df["title"].values[i] = meta_doc.find("h1").text.strip()
		df["abstract"].values[i] = meta_doc.find(
			class_="field field--name-field-abstract field--type-string-long field--label-hidden field__item").text.strip()
		df["year"].values[i] = self.extract_year(
			meta_doc.find(class_='field field--name-field-date-issued-text field--type-datetime field--label-inline clearfix').find(class_="field__item").text, df["year"].values[i])
		df["authors"].values[i] = ";".join([w.text.strip()
											for w in meta_doc.find(class_='field field--name-field-author field--type-entity-reference field--label-inline').findAll(class_="field__item")])
		df["fulltext_links"].values[i] = meta_doc.find('a', {'class': 'fdl'})['href']
		return df
		