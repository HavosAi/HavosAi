from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCampbell(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.campbellcollaboration.org"
		self.start_page = 0
		self.article_id_to_url = {}

	def prepare_query(self, query, page):
		if re.search("&start=\d+", query) == None:
			return query + "&start=%d"%(page*20)
		return re.sub("&start=\d+", "&start=%d"%(page*20), query)

	def extract_links(self, doc):
	    return  [ item['href'] for item in doc.select('.result-title a')] + [item['href'] for item in doc.select('.catItemTitle a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1].split(".html")[0]
	    if "/library/" not in article_url:
	    	article_url = self.domain_name + "/library/" +f'{article_id}.html'
	    else:
	    	article_url = self.domain_name + article_url
	    self.article_id_to_url[ f'{article_id[:80]}.html'] = article_url
	    self.fetch(
	        article_url,
	        os.path.join(folder_to_save, f'{article_id[:80]}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "Campbell"
		df["title"].values[i] = meta_doc.select("h2.itemTitle")[0].text.strip()
		df["authors"].values[i] = meta_doc.select(".itemExtraFieldsValue.itemFullTextsmall.Authors")[0].text.strip().replace(",",";")
		df["year"].values[i] = self.extract_year(meta_doc.select(".itemExtraFieldsValue.Published.date")[0].text.strip(), df["year"].values[i]) 
		df["abstract"].values[i] = meta_doc.select("div.itemIntroText")[0].text.strip()
		if df["article_name"].values[i] in self.article_id_to_url:
			df["url"].values[i] = self.article_id_to_url[df["article_name"].values[i]]
		return df