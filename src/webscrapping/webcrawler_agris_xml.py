from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerAGRIS_XML(WebCrawlerBase):
	def __init__(self):
		WebCrawlerBase.__init__(self)
		self.domain_name = "http://agris.fao.org"
		self.organisations = ["International Finance Corporation","ICIPE","AGD","RAP","IFAD, Rome", "ESA","ESA","ESC", "AGP","Bioversity", "CGIAR Consortium", "Food and Agricultural Organization of the United Nations (FAO)","International Fund for Agricultural Development (IFAD)","International Food Policy Research Institute (IFPRI)","Inter-American Institute for Cooperation on Agriculture (IICA)","Organization for Economic Cooperation and Development (OECD)", \
                 "UN Conference on Trade and Development (UNCTAD)", "UN High Level Task Force on the Food Security Crisis", "World Food Programme (WFP)", "World Trade Organization (WTO)", \
                "International Monetary Fund", "World Bank Group", "Global Partnership for Financial Inclusion", "Deutsche Gesellschaft fur Internationale Zusammenarbeit", "CTA",\
                "Independent Evaluation Group", "UN System High Level Task Force on Food Security", "International Food Policy Research Insitute"]
        self.start_page = 0

	def prepare_query(self, query, page):
		return re.sub("startIndexSearch=\d+", "startIndexSearch=%d"%(page*10), query)

	def extract_links(self, doc):
	    return  [
	        item['href']
	        for item in doc.select('div.result-item-classical > div.inner > h3 > a.title')
	    ]

	def process_article(self, article_url, folder_to_save):
	    print(article_url)
	    article_id = article_url.split('=')[-1]
	    self.fetch(
	        self.domain_name + '/agris-search/export!endNote.action?arn=' + article_id,
	        os.path.join(folder_to_save, f'{article_id}.xml')
	    )

	def prepare_initial_dataset(self, folder):
		df = WebCrawlerBase.prepare_initial_dataset(self, folder)
		df["raw_affiliation"] = ""
		df["authors_raw"] = ""
		return df

	def parse_data(self, meta_doc, tag_name):
	    return ";".join([tag.text.replace("\xa0", "").strip() for tag in meta_doc.select(tag_name)])

	def update_info(self, df, index, abstract):
	    parts = abstract.split("English Title:")
	    parts = parts[1].split("English Abstract")
	    df["title"].values[index] = parts[0].strip()
	    if len(parts) > 1:
	        self.update_abstract(df, index, parts[1])

	def update_abstract(self, df, index, abstract):
	    parts = abstract.split("Keywords:")
	    df["abstract"].values[index] = parts[0].strip()
	    if len(parts) > 1:
	        keywords = parts[1].split(df["journal_name"].values[index])[0] if df["journal_name"].values[index] != "" \
	                                                and df["journal_name"].values[index] in parts[1] else parts[1]
	        df["keywords"].values[index] = ";".join([ word.strip() for word in keywords.split(',') if word.strip() != ""])

	def fill_df_fields(self, meta_doc, df, i):
	    df["source_name"].values[i] = "Agris"
	    df["abstract"].values[i] = self.parse_data(meta_doc, "abstract")
	    df["title"].values[i] = self.parse_data(meta_doc, "title")
	    df["keywords"].values[i] = self.parse_data(meta_doc, "keyword")
	    df["authors_raw"].values[i] = self.parse_data(meta_doc, "author")
	    df["journal_name"].values[i] = self.parse_data(meta_doc, "full-title")
	    df["publisher"].values[i] = self.parse_data(meta_doc, "publisher")
	    df["year"].values[i] = self.extract_year(self.parse_data(meta_doc, "year"), df["year"].values[i])
	    df["url"].values[i] = self.parse_data(meta_doc, "web-urls")
	    if "English Title:" in df["abstract"].values[i]:
	        self.update_info(df, i, df["abstract"].values[i])
	    if "Keywords:" in df["abstract"].values[i]:
	        self.update_abstract(df, i, df["abstract"].values[i])
	    return df
	
	def get_affiliation_and_author_splitted(name, affil_word):
	    univ_search = re.search("\(.*\)", name.replace("\n", " "))
	    univ = ""
	    new_authors = ""
	    if univ_search != None and affil_word in univ_search.group(0):
	        univ = univ_search.group(0).strip()
	        new_authors = name.replace("\n", " ").replace(univ, "").strip()
	        univ = name.replace(new_authors, "")
	        univ = ";".join(filter(lambda x: x != "", [re.sub("^\d", "", normalize_simply(uni)) for uni in univ.split("\n")]))
	        new_authors = normalize_name(new_authors)
	        univ = normalize_name(univ)
	    return  univ, new_authors

	def normalize_name(name):
	    return re.sub("\s+"," ",re.sub("\(.*\)","", name).strip().split("E mail:")[0])

	def normalize_simply(name):
	    return re.sub("\s+"," ",name.replace("(", "").replace(")", "").strip())

	def contains_words_of_affiliations(author):
	    for word in ["republic", "internat", "coll.", "ministry"]:
	        if word in author.lower():
	            return True
	    return False

	def process_the_whole_dataset(df):
		for i in range(len(df)):
		    authors = []
		    affiliations = []
		    for author in df["authors_raw"].values[i].split(";"):
		        author = re.sub(r"\beng\b", " ",author).replace("(ed.)", "").replace('-', " ").strip()
		        author = re.sub("\d{2} \w{3,4} \d{4}", "", author).strip()
		        author = re.sub("\d+", "", author).strip()
		        simple_author = True
		        if author in organisations:
		            affiliations.append(normalize_simply(author))
		            simple_author = False
		        elif "FAO" in author:
		            univ, new_authors = get_affiliation_and_author_splitted(author, "FAO")
		            if univ != "" or new_authors != "":
		                affiliations.append(univ)
		                authors.append(new_authors)
		            else:
		                affiliations.append(normalize_simply(author))
		            simple_author = False
		        elif "CGIAR" in author:
		            affiliations.append(normalize_simply(author))
		            simple_author = False
		        else:
		            for word in ["Univ", "Inst", "Hochschul", "INRA", "Center", "Centre", "Council"]:
		                if word in author:
		                    univ, new_authors = get_affiliation_and_author_splitted(author, word)
		                    if univ != "" or new_authors != "":
		                        affiliations.append(univ)
		                        authors.append(new_authors)
		                        simple_author = False
		                    else:
		                        author_parts = author.split(',')
		                        for idx in range(len(author_parts)):
		                            if word in author_parts[idx]:
		                                univ = normalize_simply(",".join(author_parts[idx:]).strip())
		                                affiliations.append(univ)
		                                authors.append(normalize_name(" ".join(author_parts[:idx])))
		                                simple_author = False
		                                break
		                    break
		        if simple_author:
		            authors.append(normalize_name(author))
		    df["authors"].values[i] = ";".join([author for author in authors if author != ""])
		    df["raw_affiliation"].values[i] = ";".join([affiliation for affiliation in affiliations if affiliation != ""])
		for i in range(len(df)):
		    if not ";" in df["authors"].values[i] and df["authors"].values[i] != "":
		        if len(df["authors"].values[i].split(',')) > 2:
		            df["authors"].values[i] = df["authors"].values[i].replace(",", ";")
		        else:
		            parts = df["authors"].values[i].split(',')
		            if len(parts[0].split()) > 2:
		                df["authors"].values[i] = df["authors"].values[i].replace(",", ";")
		        df["authors"].values[i] = df["authors"].values[i].replace("ed.", "").replace(" and ", ";").replace("et al.", "").replace("Inc.", "")
		for i in range(len(df)):
		    authors = []
		    for author in df["authors"].values[i].split(";"):
		        if contains_words_of_affiliations(author):
		            if "," in author:
		                authors.append(",".join(author.split(",")[:2]))
		            print(author)
		        elif "conference" in author.lower():
		            print(author)
		        elif "depart" in author.lower():
		            print(author)
		            authors.append(author.split("Department")[0].strip())
		        else:
		            authors.append(author)
		    df["authors"].values[i] = ";".join(authors) 
		return df