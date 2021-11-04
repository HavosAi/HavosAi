from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCSIRO(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://publications.csiro.au"

	def prepare_query(self, query, page):
		if re.search("&p=\d+", query) == None:
			return query + "&p=%d"%page
		return re.sub("&p=\d+", "&p=%d"%page, query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('div.searchResultSection a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    if re.search("&pid=(\w+):([\w-]+)&",article_url) != None:
	        article_id = re.search("&pid=(\w+):([\w-]+)&",article_url).group(2)
	        self.fetch(
	            self.domain_name + article_url,
	            os.path.join(folder_to_save, f'{article_id}.html')
	        )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "CSIRO"
	    mappings = {"author":"authors", "date of publication":"year", "journal title":"journal_name", "keywords":"keywords", "publisher":"publisher",\
	       "doi":"url","abstract":"abstract"}
	    df["title"].values[i] = meta_doc.select(".content > h1")[0].text
	    for label in meta_doc.select(".pubSummaryContent label"):
	        data = label.find_next_sibling("p").text.strip()
	        column_name = label.text.replace(":","").lower().strip()
	        if column_name in mappings:
	            df[mappings[column_name]].values[i] = data
	    df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
	    df["authors"].values[i] = ";".join([w.strip() for w in df["authors"].values[i].split(";")])
	    return df
		