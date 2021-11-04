from webscrapping import webcrawler_base
from utilities import excel_writer
import re

class NalTaxonomyDownloader:

    def __init__(self):
        self.wb_base = webcrawler_base.WebCrawlerBase()

    def gather_ontology(self, start_url, adding_to_start = []):
        nal_page = self.wb_base.parse(self.wb_base.fetch(start_url))
        res = []
        try:
            text = nal_page.select("div.term strong")[0].text
            print(text)
            found = False
            for category in nal_page.select("dt"):
                if "narrower term" in category.text.lower():
                    found = True
                    class_code =  category.find_next_sibling("dd")["class"][0]
                    for narrow_item in nal_page.select("dd.%s"%class_code):
                        res.extend(
                            self.gather_ontology(
                                "https://agclass.nal.usda.gov" + narrow_item.select("a")[0]["href"], adding_to_start + [text]))
            if not found:
                res.append(adding_to_start + [text])
        except:
            pass
        return res

    def clean_ontology(self, res_ontology):
        full_res = set()
        for part in res_ontology:
            part = [term for term in part if term not in ['aquatic invertebrates',"silviculture",\
                                                          "aquatic organisms", 'freshwater crayfish', 'frozen shrimps',\
                                                         "high forest systems","underplanting","advanced regeneration",\
                                                         "second growth","strip cutting","patch cutting"]]
            for i in range(2, len(part)+1):
                part_res = part[:i]
                key_word = re.sub(r"\bculture\b","", part_res[-1]).strip()
                part_res[-1] = key_word
                res_term = [key_word]*(4-len(part_res)) + part_res[::-1]
                for i,term in enumerate(res_term):
                    res_term[i] = re.sub(r"\(.*?\)","",term).strip()
                    res_term[i] = re.sub(r"\bgood\b","",  res_term[i]).strip()
                full_res.add(tuple(res_term))
                if len(res_term) > 4:
                    print(res_term)
        return list(full_res)

    def create_ontology(self, res_list, filename):
        res = []
        for res_part in res_list:
            res.extend(self.clean_ontology(res_part))
        new_res = set()
        for i in range(len(res)):
            if len(res[i]) < 4:
                continue
            new_res.add(res[i][:2] + res[i][-2:])
            new_res.add((res[i][1],) + (res[i][1],) + res[i][-2:])
            new_res.add((res[i][2],) + (res[i][2],) + res[i][-2:])
        excel_writer.ExcelWriter().save_data_in_excel(
            list(new_res), ["narrow_name","broad_name","level_3_term","group_name"], filename)

