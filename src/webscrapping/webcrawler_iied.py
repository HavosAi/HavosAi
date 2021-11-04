from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIIED(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://pubs.iied.org"

	def prepare_query(self, query, page):
		if re.search("&p=\d+", query) == None:
			return query + "&p=%d"%(page)
		return re.sub("&p=\d+", "&p=%d"%(page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('li a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[1]
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def get_published_year(self, meta_doc):
	    year = ""
	    for li_tag in meta_doc.select(".info_blkkv_in li"):
	        if "published" in li_tag.select("span")[0].text.lower():
	            year_group = re.search("\d{4}",li_tag.text)
	            if year_group != None:
	                return year_group.group(0)
	    return year

	def get_keywords(self, meta_doc):
	    keywords = []
	    for li_tag in meta_doc.select(".info_blkkv_in li"):
	        if "theme" in li_tag.select("span")[0].text.lower() or "area" in li_tag.select("span")[0].text.lower():
	            keywords.extend([a_tag.text for a_tag in li_tag.select("a")])
	    return ";".join(keywords)

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "IIED"
	    df["title"].values[i] = meta_doc.select(".info_blkt > h1")[0].text
	    df["authors"].values[i] = ";".join([author.text.replace(",","").strip() for author in meta_doc.select(".info_blkas a")])
	    df["abstract"].values[i] = " ".join([text_tag.text.strip() for text_tag in meta_doc.select(".info_blkabs")])
	    df["year"].values[i] = self.extract_year(self.get_published_year(meta_doc), df["year"].values[i])
	    if len(meta_doc.select(".info_dlb_button a")) > 0:
	        df["url"].values[i] = self.domain_name + meta_doc.select(".info_dlb_button a")[0]["href"]
	    df["keywords"].values[i] = self.get_keywords(meta_doc)
	    return df
		