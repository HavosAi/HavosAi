from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerAGRIS(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://agris.fao.org"
		self.start_page = 0
		self.article_id_to_url = {}

	def prepare_query(self, query, page):
		if "searchIndex.do?" in query:
			query = query.replace("searchIndex.do?", "biblio.action?").replace("query=","advQuery=")
		if "searchIndex.action?" in query:
			query = query.replace("searchIndex.action?", "biblio.action?").replace("query=","advQuery=")
		if re.search("startIndexSearch=\d+", query) == None:
			return query + "&startIndexSearch=%d"%(page*10)
		return re.sub("startIndexSearch=\d+", "startIndexSearch=%d"%(page*10), query)

	def extract_links(self, doc):
	    return [
	        item['href']
	        for item in doc.select('div.result-item-classical > div.inner > h3 > a.title')
	    ]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('=')[-1]
	    self.article_id_to_url[f'{article_id}.html'] = self.domain_name + "/agris-search/" + article_url
	    self.fetch(
	        self.domain_name + "/agris-search/" + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
		df["source_name"].values[i] = "Agris"
		title_tag = [tag for tag in meta_doc.select("h1") if "AGRIS" not in tag.text][0]
		if title_tag and "[" in title_tag.text.strip():
			df["title"].values[i] = "[".join(title_tag.text.strip().split("[")[:-1]).strip()
		else:
			df["title"].values[i] = " ".join([el.text.strip() for el in meta_doc.select("h1")])
		df["authors"].values[i] = ";".join([m.text.strip() for m in meta_doc.select(".authors span")])
		if title_tag and len(title_tag.text.strip().split("[")) > 1:
			df["year"].values[i] = self.extract_year(title_tag.text.strip().split("[")[-1].strip(), df["year"].values[i])
		else:
			for m in meta_doc.select("p i"):
				if "AGRIS since" in m.text:
					df["year"].values[i] = self.extract_year(m.parent.text, df["year"].values[i])
					break
		if len(meta_doc.select("div.abstract")) > 0:
			if len(meta_doc.select("div.abstract")[0].text.strip().split("Abstract")) > 1:
				df["abstract"].values[i] = meta_doc.select("div.abstract")[0].text.strip().split("Abstract")[1].strip()
			else:
				df["abstract"].values[i] = meta_doc.select("div.abstract")[0].text.strip()
		if df["article_name"].values[i] in self.article_id_to_url:
			df["url"].values[i] = self.article_id_to_url[df["article_name"].values[i]]
		df["keywords"].values[i] = ";".join([el.text.strip() for el in meta_doc.select("a.agrovoc")])
		df["fulltext_links"].values[i] = list(set([tag["href"] for tag in meta_doc.select("a") if "title" in tag.attrs and "fulltext" in tag["title"]]))
		return df
		