from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os


class WebCrawlerCAST(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://www.cast-science.org"

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d" % (page)
		return re.sub("page=\d+", "page=%d" % (page), query)

	def extract_links(self, doc):
		return [
			item['href']
			for item in doc.select('h5 > a') if not '_qc&' in item['href']  # skip quickCAST ones
		]

	def process_article(self, article_url, folder_to_save):
		print(article_url)
		article_id = article_url.split('/')[-2]
		self.fetch(
			article_url,
			os.path.join(folder_to_save, f'{article_id}.html')
		)

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "CAST"
		df["title"].values[i] = meta_doc.find(class_="page-title bb-title text-white").text
		df["abstract"].values[i] = meta_doc.find(class_="container pt-5 pb-5").get_text(separator=u';')
		df["year"].values[i] = self.extract_year(df["abstract"].values[i], df["year"].values[i])
		return df
