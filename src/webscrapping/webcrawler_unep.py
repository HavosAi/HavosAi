from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerUNEP(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://wedocs.unep.org/"

	def prepare_query(self, query, page):
		if re.search("&page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("&page=\d+", "&page=%d"%(page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('.artifact-description a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.fetch(
	        self.domain_name + article_url + "?show=full",
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "UNEP"
	    df["authors"].values[i] = ""
	    df["keywords"].values[i] = ""
	    for m in meta_doc.select("td.text-info"):
	        if "title" in m.text:
	            df["title"].values[i] = m.find_next_sibling("td").text.strip()
	        if "subject" in m.text:
	            df["keywords"].values[i] = self.add_to_keywords(df["keywords"].values[i], m.find_next_sibling("td").text.strip())
	        if "author" in m.text or "creator" in m.text:
	            df["authors"].values[i] = self.add_to_keywords(df["authors"].values[i], m.find_next_sibling("td").text.strip())
	        if "description" in m.text:
	            df["abstract"].values[i] = m.find_next_sibling("td").text.strip()
	        if "identifier.uri" in m.text:
	            df["url"].values[i] = m.find_next_sibling("td").text.strip()
	        if "publisher" in m.text:
	            df["publisher"].values[i] = m.find_next_sibling("td").text.strip()
	        if "date" in m.text:
	        	df["year"].values[i] = self.extract_year(m.find_next_sibling("td").text.strip(), df["year"].values[i])
	    return df
		