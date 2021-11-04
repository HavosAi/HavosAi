from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerWHO(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://apps.who.int"

	def prepare_query(self, query, page):
		if re.search("&page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("&page=\d+", "&page=%d"%(page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('.artifact-title a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )
	
	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "WHO"
	    df["authors"].values[i] = ";".join([ m.text for m in meta_doc.select("#citation-article-authors span")])
	    df["year"].values[i] = self.extract_year(meta_doc.select("#citation-article-date")[0].text, df["year"].values[i])
	    df["title"].values[i] = meta_doc.select("#citation-article-title")[0].text.strip()
	    if len(meta_doc.select("#citation-publisher")) > 0:
	        df["publisher"].values[i] = meta_doc.select("#citation-publisher")[0].text.strip()
	    df["url"].values[i] = meta_doc.select("#citation-article-identifier a")[0]["href"]
	    for m in meta_doc.select("div.simple-item-view-other.item-page-field-wrapper h5"):
	        if "abstract" in m.text.lower():
	            df["abstract"].values[i] = " ".join([text.strip() for text in m.parent.find_all(text=True, recursive = False) if text.strip() != ""])
	    df = self.fill_year_if_not_found(df, i)
	    return df