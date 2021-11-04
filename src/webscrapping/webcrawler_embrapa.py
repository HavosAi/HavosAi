from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerEMBRAPA(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "https://www.embrapa.br"

	def check_url(self, url):
		if re.search(r"https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/busca/.+\??.*", url) != None:
			return ""
		return "Url should contain keywords. For example, this url https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/busca/smallholder+farming?p_auth=pEVc36Iv&_buscapublicacao_WAR_pcebusca6_1portlet_keywords=&_buscapublicacao_WAR_pcebusca6_1portlet_advancedSearch=false&_buscapublicacao_WAR_pcebusca6_1portlet_delta=10&_buscapublicacao_WAR_pcebusca6_1portlet_resetCur=false&_buscapublicacao_WAR_pcebusca6_1portlet_andOperator=true&_buscapublicacao_WAR_pcebusca6_1portlet_cur=1 is ok."

	def prepare_query(self, query, page):
		if re.search("portlet_cur=\d+", query) == None:
			return query + "portlet_cur=%d"%(page)
		return re.sub("portlet_cur=\d+", "portlet_cur=%d"%(page), query)

	def extract_links(self, doc):
		return [item['href'] for item in doc.select('div.titulo a')]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('/')[-2]
	    self.fetch(
	        self.domain_name + article_url if self.domain_name not in article_url else article_url,
	        os.path.join(folder_to_save, f'{article_id}.html')
	    )

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "EMBRAPA"
	    mappings = {"autoria":"authors", "ano de publicação":"year", "unidade":"journal_name", "palavras-chave":"keywords", "resumo":"abstract"}
	    df["title"].values[i] = meta_doc.select("h1.titulo")[0].text.strip()
	    if len(meta_doc.select("div.botoes a.baixar-publicacao")) > 0:
	    	df["url"].values[i] = meta_doc.select("div.botoes a.baixar-publicacao")[0]["href"]
	    for label in meta_doc.select("div.grupos span.label"):
	        if label.find_next_sibling("span") == None:
	            data = ";".join([item.text for item in label.parent.select("a")])
	        else:
	            data = label.find_next_sibling("span").text.strip()
	        column_name = label.text.replace(":","").lower().strip()
	        if column_name in mappings:
	            df[mappings[column_name]].values[i] = data
	    df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
	    return df
		