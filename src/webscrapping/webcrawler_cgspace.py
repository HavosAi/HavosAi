from webscrapping.webcrawler_base import WebCrawlerBase
import re
import os

class WebCrawlerCGSPACE(WebCrawlerBase):
    def __init__(self):
        WebCrawlerBase.__init__(self)
        self.domain_name = "https://cgspace.cgiar.org"
        self.start_page = 1

    def prepare_query(self, query, page):
        if re.search("page=\d+", query) == None:
            return query + "&page=%d"%page
        return re.sub("page=\d+", "page=%d"%(page), query)

    def extract_links(self, doc):
        return  [
            self.domain_name + item['href'] + "?show=full"
            for item in doc.select('a.description-info')
        ]

    def process_article(self, article_url, folder_to_save):
        print(article_url)
        article_id = "_".join(article_url.split("?")[0].split('/')[-2:])
        self.fetch(
            article_url,
            os.path.join(folder_to_save, f'{article_id}.html')
        )

    def fill_df_fields(self, meta_doc, df, i):
        df["source_name"].values[i] = "CGIAR sgspace"
        mappings = {"dc.contributor.author": "authors", "dc.creator": "authors", "dc.date.issued": "year",
            "dc.identifier.uri": "url", "dc.description.abstract": "abstract", "dc.publisher": "publisher",
            "cg.subject": "keywords", "dc.subject": "keywords", "dc.title": "title", "cg.coverage": "keywords",
            "cg.contributor.center": "affiliation", "dc.source": "journal_name", "cg.contributor.affiliation": "affiliation",
            "cg.place": "keywords"}
        for row in meta_doc.select("tr.ds-table-row"):
            column_name = row.select("td")[0].text.strip()
            if column_name not in mappings:
                column_name = ".".join(column_name.split(".")[:-1])
            if column_name not in mappings:
                continue
            column_name = mappings[column_name]
            text = row.select("td")[1].text.strip()
            if column_name == "keywords":
                text = text.lower()
            if df[column_name].values[i].strip() == "":
                df[column_name].values[i] = text
            else:
                df[column_name].values[i] = df[column_name].values[i] + " ; " + text
        df["year"].values[i] = self.extract_year(df["year"].values[i], df["year"].values[i])
        return df
        