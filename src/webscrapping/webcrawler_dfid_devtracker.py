from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os
import pandas as pd

class WebCrawlerDFIDDevtracker(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://devtracker.dfid.gov.uk"
		self.article_id_2_url = {}
		self.articles_info = {}
		self.additional_urls = []

	def append_more_data(self, df):
		new_df = pd.DataFrame( {'article_name': ['additional']*len(self.additional_urls)})
		df = pd.concat([df, new_df], axis=0).fillna("")
		for i in range(len(df) - len(new_df), len(df)):
			url = self.additional_urls[i - len(df) + len(new_df)]
			obj = self.articles_info[url]
			df["source_name"].values[i] = "DFID devtracker"
			df["title"].values[i] = " ".join([t.text.strip() for t in obj.select("h3")])
			df["abstract"].values[i] = " ".join([t.text.strip() for t in obj.select("p.description")])
			df["affiliation"].values[i] = " ".join([t.text.strip() for t in obj.select("span.reporting-org")])
			for span_text in obj.select("div.bottom-table span"):
				if "start date" in span_text.text.lower():
					df["year"].values[i] = self.extract_year(span_text.text, df["year"].values[i])
					break
			df["url"].values[i] = self.domain_name + url
		return df

	def prepare_query(self, query, page):
		if re.search("#page-\d+", query) == None:
			return query + "#page-%d"%(page)
		return re.sub("#page-\d+", "#page-%d"%(page), query)

	def extract_links(self, doc):
	    links = [
	        item['href']
	        for item in doc.select('div.search-result a')
	    ]
	    for idx, obj in enumerate(doc.select('div.search-result')):
	    	self.articles_info[links[idx]] = obj
	    return links

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.article_id_2_url[f'{article_id}.html'] = article_url
	    result = self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )
	    if result.strip() == "" and article_url in self.articles_info:
	    	self.additional_urls.append(article_url)

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "DFID devtracker"
	    df["title"].values[i] = ";".join([d.text.strip() for d in meta_doc.select("div#page-title h1")])
	    df["year"].values[i] = self.extract_year(
	    	";".join([d.text.strip() for d in meta_doc.select("p.last-updated")]), df["year"].values[i])
	    df["abstract"].values[i] = "\n".join([d.text.strip() for d in meta_doc.select("p.project-description")])
	    df["keywords"].values[i] = ";".join([d.text.strip().split("\n")[0] for d in meta_doc.select("div.project-country-title")])
	    df["affiliation"].values[i] = ";".join([d.text.strip() for d in meta_doc.select("div#implementing-organisations li")] +\
	    	[d.text.strip() for d in meta_doc.select("div.more-info-container a") if d.text.strip()])
	    df["url"].values[i] = self.domain_name + self.article_id_2_url[df["article_name"].values[i]]
	    return df
		