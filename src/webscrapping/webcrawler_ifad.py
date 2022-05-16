from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerIFAD(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://www.ifad.org"
        self.headers = {'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

    def prepare_query(self, query, page):
        if re.search("&start=\d+", query) == None:
            return query + "&start=%d"%(page)
        return re.sub("&start=\d+", "&start=%d"%(page), query)

    def extract_links(self, doc):
        return [item['href'].split('?')[0] for item in doc.select('div.list-group-title a')]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = article_url.split('/')[-1].split('?')[0]
        self.fetch(
            article_url,
            os.path.join(folder_to_save, f'{article_id}.html'),
            custom_headers=self.headers
        )

    def getText(self, parent):
        return ''.join(parent.find_all(text=True, recursive=False)).strip()

    def get_authors_and_affiliations(self, meta_doc):
        authors = []
        affiliations = []
        full_string = ""
        for tag in meta_doc.select(".pub-row > .pub-row-title"):
            if "author" in tag.text.lower():
                full_string = re.sub(r"\band\b", ",", tag.find_next_siblings()[0].text)
                break
        for match in re.findall("\(.*?\)",full_string):
            if not "consultant" in match.lower():
                match = match.replace("(","").replace(")","").strip()
                affiliations.append(match)
        full_string = re.sub("\(.*?\)","",full_string)
        for author in full_string.split(","):
            author = author.strip()
            if author != "":
                if author.upper() == author or "university" in author.lower() or "institute" in author.lower():
                    affiliations.append(author)
                else:
                    authors.append(author)
        return ";".join(authors), ";".join(affiliations)

    def get_keywords(self, meta_doc):
        for tag in meta_doc.select(".pub-row > .pub-row-title"):
            if "topic" in tag.text.lower():
                return tag.find_next_siblings()[0].text.replace(",",";")
        return ""

    def get_article_url(self, meta_doc):
        if len(meta_doc.select(".download-button")) > 0:
            return "https://www.ifad.org" + meta_doc.select(".download-button")[0]["href"]
        for tag in meta_doc.select("button"):
            if "download" in tag.text.lower():
                return re.search("http.+", tag["onclick"]).group(0).strip().replace("\"","").replace("'","")
        return ""

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "IFAD"
        df["title"].values[i] = self.getText(meta_doc.select(".pub-header > h1")[0])
        if len(meta_doc.select(".pub-header > h1 > div")) > 0:
            df["year"].values[i] = self.extract_year(meta_doc.select(".pub-header > h1 > div")[0].text, df["year"].values[i])
        if len(meta_doc.select(".main-content")) > 0:
            df["abstract"].values[i] = meta_doc.select(".main-content")[0].text.strip()
        authors,affiliations = self.get_authors_and_affiliations(meta_doc)
        df["authors"].values[i] = authors
        df["affiliation"].values[i] = affiliations
        df["url"].values[i] = self.get_article_url(meta_doc)
        df["keywords"].values[i] = self.get_keywords(meta_doc)
        return df

