from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerWFP(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www1.wfp.org"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("&page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("&page=\d+", "&page=%d"%(page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('.db.lh-heading.fs4 a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.fetch(
	        article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "WFP"
	    df["title"].values[i] = meta_doc.select("h1.lh-heading")[0].text.strip()
	    if len(meta_doc.select("div.field.field--body.mb4")) > 0:
	        df["abstract"].values[i] = meta_doc.select("div.field.field--body.mb4")[0].text.strip()
	    if len(meta_doc.select("div.summary.mb4")) > 0:
	        df["abstract"].values[i] = meta_doc.select("div.summary.mb4")[0].text.strip()
	    if len(meta_doc.select(".field--field-topics a")) > 0:
	        df["keywords"].values[i] = self.add_to_keywords(df["keywords"].values[i], ";".join([m.text.strip() for m in meta_doc.select(".field--field-topics a")]))
	    if len(meta_doc.select(".field--field-country a")) > 0:
	        df["keywords"].values[i] = self.add_to_keywords(df["keywords"].values[i], ";".join([m.text.strip() for m in meta_doc.select(".field--field-country a")]))
	    if len(meta_doc.select(".mv2 a")) > 0:
	        df["url"].values[i] = meta_doc.select(".mv2 a")[0]["href"]
	    if len(meta_doc.select(".mb2 a")) > 0:
	        df["url"].values[i] = meta_doc.select(".mb2 a")[0]["href"]
	    df["year"].values[i] = self.extract_year(meta_doc.select(".field--field-publication-date")[0].text, df["year"].values[i])
	    df["authors"].values[i] = ";".join([m.text.strip() for m in meta_doc.select(".field--field-publication-author span")])
	    return df
		