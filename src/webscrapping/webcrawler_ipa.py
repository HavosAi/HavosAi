from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIPA(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.poverty-action.org"
		self.start_page = 0
		self.article_id_2_url = {}

	def prepare_query(self, query, page):
		if re.search("page=\d+", query) == None:
			return query + "&page=%d"%(page)
		return re.sub("page=\d+", "page=%d"%(page), query)

	def extract_links(self, doc):
	    return  [ item['href'] for item in doc.select('span.field-content a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-1]
	    self.article_id_2_url[f'{article_id}.html'] = self.domain_name + article_url
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def get_keywords_by_class_name(self, meta_doc, class_name):
	    if len( meta_doc.select(class_name)) == 0:
	        return ""
	    keywords_area = meta_doc.select(class_name)[0]
	    if len(keywords_area.select("div.field-items > div")) > 0:
	        return ";".join([tag.text for tag in keywords_area.select("div.field-items > div")])
	    return ""

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "IPA"
	    df["title"].values[i] = meta_doc.select("h1.title")[0].text
	    abstract = ""
	    if len(meta_doc.select("div.field-name-field-description")) > 0:
	        abstract_area = meta_doc.select("div.field-name-field-description")[0]
	        if len(abstract_area.select("div.field-item.even > p")) > 0:
	            abstract = abstract + " " + abstract_area.select("div.field-item.even > p")[0].text
	        if len(abstract_area.select("div.field-item.even > div")) > 0:
	            abstract = abstract + " " + abstract_area.select("div.field-item.even > div")[0].text
	    df["abstract"].values[i] = abstract.strip()
	    if len(meta_doc.select("div.field-name-field-date")) > 0:
	        date_area = meta_doc.select("div.field-name-field-date")[0]
	        if len(date_area.select("div.field-item.even")) > 0:
	            df["year"].values[i] = self.extract_year(date_area.select("div.field-item.even")[0].text, df["year"].values[i])
	    keywords = ""
	    country_keywords = self.get_keywords_by_class_name(meta_doc, "div.field-name-field-country")
	    if country_keywords != "":
	        keywords = keywords + country_keywords + ";"
	    program_area_keywords = self.get_keywords_by_class_name(meta_doc, "div.field-name-field-program-area")
	    if program_area_keywords != "":
	        keywords = keywords + program_area_keywords + ";"
	    topics_keywords = self.get_keywords_by_class_name(meta_doc, "div.field-name-field-topics")
	    if topics_keywords != "":
	        keywords = keywords + topics_keywords + ";"
	    df["keywords"].values[i] = keywords
	    df["journal_name"].values[i] = self.get_keywords_by_class_name(meta_doc, "div.field-name-field-journal")
	    df["authors"].values[i] = self.get_keywords_by_class_name(meta_doc, "div.field-name-field-authors")
	    if len(meta_doc.select("div.view-publication")) > 0:
	        view_publication_area = meta_doc.select("div.view-publication")[0]
	        if len(view_publication_area.select("a")) > 0:
	            df["url"].values[i] = view_publication_area.select("a")[0]["href"]
	    else:
	        df["url"].values[i] = self.article_id_2_url[df["article_name"].values[i]]
	    return df