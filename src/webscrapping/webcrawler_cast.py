from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCAST(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://www.cast-science.org"

	def prepare_query(self, query, page):
		if re.search("&page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("&page=\d+", "&page=%d"%(page), query)

	def extract_links(self, doc):
	    return  [
	        item['href']
	        for item in doc.select('td.description h3 a')
	        if not '_qc&' in item['href'] # skip quickCAST ones
	    ]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('?')[-1].split('=')[-1]
	    self.fetch(
	        self.domain_name + "/publications/publications"+ article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "CAST"
	    df["title"].values[i] = meta_doc.select("div.header")[0].text.strip()
	    if len(meta_doc.select("td.description > p")) > 0:
	        text = meta_doc.select("td.description > p")[0].text
	        text = re.sub(r"([.])(?=,)", "#", text)
	        text = re.sub(r"(?<=(\b\w\w))([.])", "#", text)
	        text = re.sub(r"(?<=(\b\w))([.])", "#", text)
	        text = re.sub(r"# ?(?=\w+ ?\d+)", ".", text)
	        sentences = list(filter(None, re.split(r"[.!?]+", text)))
	        found = False
	        for j in range(len(sentences)):
	            sentence = sentences[j]
	            if re.search("[Aa]uthor[s]?:|[Cc]hair[s]?:", sentence) != None:
	                found = True
	                df["abstract"].values[i] = text.split(sentence.split(":")[0])[0].replace("#",".")
	                authors = []
	                affiliations = []
	                for author in sentence.split(":")[1].split(";"):
	                    for author1 in author.split("and"):
	                        authors.append(author1.split(",")[0].strip().replace("#","."))
	                        affiliations.append(",".join(author1.split(",")[1:]).strip().replace("#","."))
	                df["authors"].values[i] = ";".join(authors)
	                df["affiliation"].values[i] = ";".join(affiliations)
	                if j != len(sentences) - 1:
	                    for sent in sentences[j+1:]:
	                        year = re.search(r"\b\d{4}\b", sent)
	                        if year != None:
	                            df["year"].values[i] = year.group(0)
	                            break
	                break
	        if not found:
	            df["abstract"].values[i] = text.strip()
	    df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
	    return df
		