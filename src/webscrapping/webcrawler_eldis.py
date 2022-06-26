from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerEldis(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.eldis.org"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d" % (page)
		return re.sub("page=\d+", "page=%d" % (page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('h3 > a')]

	def process_article(self, article_url, folder_to_save):
		print(article_url)
		article_id = article_url.split('/')[-1]
		self.fetch(
			self.domain_name + article_url,
			os.path.join(folder_to_save, f'{article_id}.html')
		)

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "Eldis"
		df["title"].values[i] = meta_doc.find(class_="panel-pane pane-idscontent-doc-content-type").find("h2").text.strip()
		df["abstract"].values[i] = meta_doc.find(class_="field-description").text.strip()
		df["year"].values[i] = self.extract_year(meta_doc.find(class_="field-publication_date").text.strip(),
												 df["year"].values[i])
		df["authors"].values[i] = ";".join([w.text.strip()
											for w in meta_doc.findAll(class_="author")])
		df["keywords"].values[i] = ";".join([w.text.strip()
											for w in meta_doc.find(class_="related-themes-list related-categories-list").findAll("li")])
		df["fulltext_links"].values[i] = meta_doc.find('a', {'class': 'download-link btn'})['href']
		return df
		