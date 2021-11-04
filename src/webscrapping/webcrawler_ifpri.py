from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIFPRI(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://ebrary.ifpri.org"

	def prepare_query(self, query, page):
		return re.sub("/page/\d+", "/page/%d"%(page), query)

	def extract_links(self, doc):
	    return  [ item['href'] for item in doc.select('li.listItem > ul > li > div.marginTopTextAdjuster > a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = '_'.join(article_url.split('/')[-6:])
	    self.fetch(
	        self.domain_name + article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def parse_data(self, meta_doc, tag_name):
	    return ";".join([tag.text.replace("\xa0", "").strip() for tag in meta_doc.select(tag_name)])

	def parse_data_several_tags(self, meta_doc, tag_names):
	    return " ".join([ self.parse_data(meta_doc, tag_name) for tag_name in tag_names]).strip()

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "IFPRI"
	    meta_doc = meta_doc.select("div#details_accordion > div")[0]
	    df["title"].values[i] = self.parse_data_several_tags(meta_doc, ["td#metadata_title", "td#metadata_subtit", "td#metadata_object_title", "td#metadata_object_subtit"])
	    df["authors"].values[i] = self.parse_data_several_tags(meta_doc,["td#metadata_creato > a", "td#metadata_object_creato > a"])
	    df["year"].values[i] = self.extract_year(self.parse_data_several_tags(meta_doc,["td#metadata_date", "td#metadata_object_date"]), df["year"].values[i])
	    df["keywords"].values[i] = self.parse_data_several_tags(meta_doc,["td#metadata_loc > a", "td#metadata_object_loc > a"])
	    df["url"].values[i] = self.parse_data_several_tags(meta_doc,["td#metadata_doi", "td#metadata_object_web", "td#metadata_web"])
	    df["abstract"].values[i] = self.parse_data_several_tags(meta_doc,["td#metadata_descri", "td#metadata_object_descri"])
	    df["journal_name"].values[i] = self.parse_data_several_tags(meta_doc, ["td#metadata_series", "td#metadata_object_series"])
	    df["publisher"].values[i] = self.parse_data_several_tags(meta_doc, ["td#metadata_publis","td#metadata_object_publis"])
	    return df
		