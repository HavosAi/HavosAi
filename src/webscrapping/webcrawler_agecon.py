from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerAGECON(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://ageconsearch.umn.edu"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("&jrec=\d+", query) == None:
			return query + "&jrec=%d"%(page*10+1)
		return re.sub("&jrec=\d+", "&jrec=%d"%(page*10+1), query)

	def extract_links(self, doc):
		return [item['href'].split("files/")[0] for item in doc.select('div.result-row a') if item['href'].startswith("/record/")]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-2]
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "AgEcon"
	    df["title"].values[i] = meta_doc.select("h2.record-title")[0].text.strip()
	    if len(meta_doc.select("div.record-authors")) > 0:
	    	df["authors"].values[i] = meta_doc.select("div.record-authors")[0].text.strip()
	    df["abstract"].values[i] = ""
	    if len(meta_doc.select("p.record-full-abstract")) > 0:
	        df["abstract"].values[i] += meta_doc.select("p.record-full-abstract")[0].text.strip()
	    df["url"].values[i] = "https://ageconsearch.umn.edu/record/"+ df["article_name"].values[i].split(".")[0] +"/"
	    df["keywords"].values[i] = ""
	    for meta_data in meta_doc.select("div.record-meta-key"):
	        if "issue date" in meta_data.text.lower():
	        	df["year"].values[i] = self.extract_year(meta_data.find_next_sibling("div").text, df["year"].values[i])
	        if "keyword" in meta_data.text.lower():
	            df["keywords"].values[i] = self.add_to_keywords(df["keywords"].values[i],meta_data.find_next_sibling("div").text.strip())
	        if "subject" in meta_data.text.lower():
	            df["keywords"].values[i] = self.add_to_keywords(df["keywords"].values[i],";".join([m.text.strip() for m in meta_data.find_next_sibling("div") if m.text.strip() != ""]))
	        if "note" in meta_data.text.lower():
	            df["abstract"].values[i] = self.add_to_keywords(df["abstract"].values[i],meta_data.find_next_sibling("div").text.strip())
	    return df
		