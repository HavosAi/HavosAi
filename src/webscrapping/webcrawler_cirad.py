from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os
import bs4

class WebCrawlerCIRAD(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://agritrop.cirad.fr"
		self.start_page = 0

	def prepare_query(self, query, page):
		if re.search("&search_offset=\d+", query) == None:
			return query + "&search_offset=%d"%(page*20)
		return re.sub("&search_offset=\d+", "&search_offset=%d"%(page*20), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('tr.ep_search_result a') if item["href"].startswith(self.domain_name)]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-2]
	    self.fetch(
	        article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "CIRAD"
	    df["title"].values[i] = meta_doc.select("h1.ep_tm_pagetitle")[0].text.strip()
	    text = " ".join([t for t in meta_doc.select(".ep_summary_content_main > p")[0].contents if type(t)==bs4.element.NavigableString])
	    df["year"].values[i] = self.extract_year(" ".join(text.split(".")[:2]), df["year"].values[i])
	    if len(meta_doc.select("p.summary_champs.summary_resume")) > 0:
	        df["abstract"].values[i] = ":".join(meta_doc.select("p.summary_champs.summary_resume")[0].text.split(":")[1:]).strip()
	    for span in meta_doc.select("p.summary_champs > span"):
	        if "auteurs et affiliations" in span.text.lower():
	            author_list = span.parent.find_next_sibling("ul")
	            authors = []
	            affiliations = set()
	            for au in author_list.select("li"):
	                author = au.text.split(",")[0].strip()
	                if author != "":
	                    authors.append(author)
	                affiliation = ",".join(au.text.split(",")[1:]).strip()
	                if affiliation != "":
	                    affiliations.add(affiliation)
	            df["authors"].values[i] = ";".join(authors)
	            df["affiliation"].values[i] = ";".join(list(affiliations))
	    df["url"].values[i] = "http://agritrop.cirad.fr/" + df["article_name"].values[i].split(".")[0] + "/"
	    return df
		