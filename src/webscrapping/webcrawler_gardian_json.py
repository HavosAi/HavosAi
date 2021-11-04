from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os
import requests
import json

class WebCrawlerGARDIAN_JSON(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://gardian.bigdata.cgiar.org"

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article['_source']['publication_id']
	    file_path = os.path.join(folder_to_save, f'/{article_id}.json')
	    web_link = self.domain_name + f'/publication.php?id={article_id}'

	    article['__custom'] = {'web_link': web_link}
	    
	    with open(file_path, 'w') as outfile:
	        json.dump(article, outfile, sort_keys=True, indent=4)

	def process_page(self, page, query, folder_to_save, added_ids_from_previous_page):
	    print(f'\n\nPage {page}')

	    response = requests.post('http://gardian.bigdata.cgiar.org/php_elastic/search_publication_advanced.php',
               data={
                   'keywords': query,
                   'from': page,
                   'facet': 1,
                   'country': 'none',
                   'soption': 'and',
                   'year': 'none',
                   'center': 'none',
                   'field': '_all',
                   'type': 'none',
                   'sort': 'relevance'
               })   

	    response.raise_for_status()
	    json = response.json()        
	    
	    hits = json['publications']['hits']['hits']
	    n_hits = len(hits)
	    print(f'Hits {n_hits}')
	    self.sleep(3)
	    
	    for article in hits:
	        self.process_article(article, folder_to_save)
	    
	    return n_hits > 0, added_ids_from_previous_page

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "Gardian"
	    df["abstract"].values[i] = jsn["cg.description"]
	    df["title"].values[i] = jsn["cg.title"]
	    df["keywords"].values[i] = ";".join([word for word in jsn["cg.subject.topics"] if word != None])
	    df["authors"].values[i] = jsn["cg.creator"].replace(",", ";")
	    df["year"].values[i] = self.extract_year(jsn["cg.date.production"], df["year"].values[i])
	    df["url"].values[i] = jsn["cg.identifier.url"][0]
	    df["raw_affiliation"].values[i] = ";".join(jsn["cg.contributor"])
	    return df

	def process_file(self, f):
		return json.loads(f.read())["_source"]
		