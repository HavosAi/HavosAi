from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCEE(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://www.environmentalevidence.org"

	def prepare_query(self, query, page):
		if re.search("/page/\d+", query) == None:
			return query + "/page/%d"%(page)
		return re.sub("/page/\d+", "/page/%d"%(page), query)

	def extract_links(self, doc):
	    urls = []
	    articles = [
	        item
	        for item in doc.select('div.crev-box')
	    ]
	    for article in articles:
	        url = article.select("h2 > a")
	        if len(url) > 0:
	            year = re.search("\d{4}", article.select("p")[0].text if len(article.select("p")) > 0 else "")
	            urls.append((url[0]["href"], year.group(0) if year != None else ""))
	    return urls

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url[0].split('/')[-1][:100] + "_" + article_url[1]
	    print(article_url[0].split('/')[-1])
	    self.fetch(
	        article_url[0],
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def parse_data(self, meta_doc, tag_name):
	    return ";".join([tag.text.replace("\xa0", "").strip() for tag in meta_doc.select(tag_name)])

	def find_abstract(self, meta_doc, title):
	    abstract = " ".join([tag.text for tag in meta_doc.select("div.collapsible-content") + meta_doc.select("div.AbstractSection")])
	    if len(meta_doc.select("span.H4")) > 0:
	        abstract = abstract + " " + meta_doc.select("span.H4")[0].parent.text
	        abstract = abstract + " " + " ".join(tag.text for tag in meta_doc.select("span.H4")[0].parent.next_sibling.next_sibling.select(".B1"))
	    if abstract == '':
	        abstract = " ".join([tag.next_sibling.next_sibling.text for tag in meta_doc.select("h3") if tag.text == "Abstract"])
	    if abstract == '':
	        abstract = " ".join([tag.next_sibling.next_sibling.text for tag in meta_doc.select("h2") if tag.text == title])
	    return abstract.replace("\xa0", "").strip()

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "CEE"
	    df["title"].values[i] = self.parse_data(meta_doc, "title")
	    df["abstract"].values[i] = self.find_abstract(meta_doc, df["title"].values[i])
	    df["authors"].values[i] = self.parse_data(meta_doc, "span.rev-team-name")
	    df["keywords"].values[i] = (";".join([tag.next_sibling.next_sibling.text for tag in meta_doc.select("h3") if tag.text == "Keywords"])).replace(",",";")
	    url_tags = meta_doc.select("ul.doc-links > li > a")
	    df["url"].values[i] = url_tags[1]["href"] if len(url_tags) >= 2 else url_tags[0]["href"]
	    df["year"].values[i] = self.extract_year(df["article_name"].values[i].split(".html")[0].split("_")[-1], df["year"].values[i])
	    return df
		