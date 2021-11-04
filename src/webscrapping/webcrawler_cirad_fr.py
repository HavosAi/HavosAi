from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCIRAD_fr(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.cirad.fr"
		self.article_id_to_url = {}
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("/(offset)/\d+", query) == None:
			return query + "/(offset)/%d"%(page*10)
		return re.sub("/(offset)/\d+", "/(offset)/%d"%(page*10), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('ul.resultList.blockXml a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.article_id_to_url[f'{article_id}.html'] = self.domain_name + article_url
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "CIRAD"
	    df["title"].values[i] = meta_doc.select("div.page h1")[0].text.strip()
	    df["year"].values[i] = self.extract_year(meta_doc.select("p.date")[0].text, df["year"].values[i])
	    df["abstract"].values[i] = ""
	    if len(meta_doc.select("div.short_description")) > 0:
	        df["abstract"].values[i] += meta_doc.select("div.short_description").text.strip()
	    if len(meta_doc.select("div.description")) > 0:
	        df["abstract"].values[i] += meta_doc.select("div.description").text.strip()
	    if df["article_name"].values[i] in self.article_id_to_url:
	    	df["url"].values[i] = self.article_id_to_url[df["article_name"].values[i]]
	    return df
		