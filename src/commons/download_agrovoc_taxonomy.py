import zeep
import time
import re
from utilities import excel_writer, utils

class TermInfo:
    def __init__(self, broad_name, term_code, narrow_items, parent_name):
        self.broad_name = broad_name
        self.term_code = term_code
        self.narrow_items = narrow_items
        self.parent_name = parent_name

class AgrovocTaxonomyDownloader:

    def __init__(self):
        wsdl = 'http://agrovoc.uniroma2.it:8080/SKOSWS/services/SKOSWS?wsdl'
        self.client = zeep.Client(wsdl=wsdl)

    def search_narrow_items_for_term(self, term_code="", term_name="", chosen_language="en"):
        if term_code == "":
            search_item = term_name
            terms_info = [term.replace('[', '').strip() for term in self.client.service.simpleSearchByMode2(
                searchString=search_item, searchmode="exact", separator=' ').split()[:-2]]
            if len(terms_info) > 0:
                term_code = terms_info[0]
            else:
                print(term_name + " not found")
                return []
        else:
            term_name = self.client.service.getTermByLanguage(termcode=term_code,language=chosen_language)
        narrow_terms = []
        if term_name != None:
            print("")
            print(term_name, term_code)
            print("")
            print("Narrower items: ")
            narrow_items = [term.replace(']','').strip() for term in self.client.service.getConceptInfoByTermcode(
                termCode=term_code)[-2].split(',')[1:]]
            for rel_item in narrow_items:
                name = self.client.service.getTermByLanguage(termcode=rel_item,language=chosen_language)
                if name != None:
                    print(name, rel_item)
                    narrow_terms.append((rel_item, name))
            narrow_terms.append((term_code, term_name))
        return narrow_terms

    def get_narrow_items_for_term(self, term_code="", term_name="", chosen_language="en"):
        requested = True
        product_narrow_items = []
        trials = 5
        while requested == True:
            if trials < 0:
                break
            try:
                product_narrow_items = self.search_narrow_items_for_term(
                    term_code,term_name, chosen_language = chosen_language)
                requested = False
                break
            except:
                print("Connection refused by the server..")
                time.sleep(5)
                trials -= 1
                continue
        return product_narrow_items

    def try_parse_code(self, code):
        try:
            int_code = int(code)
        except:
            int_code = 10^10
        return int_code

    def calculate_jaccard(self, set_1, set_2):
        if(len(set_1.union(set_2))== 0):
            return 0
        return len(set_1.intersection(set_2))/len(set_1.union(set_2))

    def merge_two_sets(self, set_1, set_2):
        return set_1.union(set_2)

    def deduplicate_words(self, name):
        words = set()
        res = []
        for word in name.split():
            word = word.strip()
            if word not in words:
                words.add(word)
                res.append(word)
        return " ".join(res)

    def normalize_name(self, name):
        initial_name = name
        pattern = r"[^\w]|\b\w\b|\b\d\b"
        if "," in name:
            name = name.split(',')[0].strip()
        name = name.replace('-','')
        name = re.sub("\(.*?\)", " ", name).strip()
        res = self.deduplicate_words(" ".join((re.sub(pattern, " ", name).split())))
        return res

    def get_narrow_items_level_2(self, level_2_narrow_items, chosen_language="en"):
        narrow_items = {}
        for narrow_item_code, narrow_item_name in level_2_narrow_items:
                narrow_list = self.get_narrow_items_for_term(
                    term_code = narrow_item_code, chosen_language = chosen_language)
                narrow_items[narrow_item_name] = narrow_list

        return narrow_items

    def translate_word(self, word, code = None, chosen_language="en"):
        if code is None:
            search_item = word
            terms_info = [term.replace('[', '').strip() for term in self.client.service.simpleSearchByMode2(
                searchString=search_item, searchmode="exact", separator=' ').split()[:-2]]
            if len(terms_info) > 0:
                term_code = terms_info[0]
                term_name = self.client.service.getTermByLanguage(
                    termcode=term_code,language=chosen_language)
                return term_name if term_name is not None else word
            else:
                return word
        else:
            term_name = self.client.service.getTermByLanguage(termcode=code,language=chosen_language)
            if term_name is not None:
                return term_name
            else:
                return word

    def find_narrow_items_level_4(self, narrow_items, chosen_language="en"):
        dict_products = {}
        for level_3_name in narrow_items:
            for (product_code, product_name) in narrow_items[level_3_name]:
                product_name = self.normalize_name(self.translate_word("", code=product_code, chosen_language="en"))
                if product_name not in dict_products:
                    dict_products[product_name] = TermInfo(product_name, self.try_parse_code(product_code), set([product_name]), \
                                                           self.normalize_name(self.translate_word(level_3_name, chosen_language="en")))
                product_narrow_items = self.get_narrow_items_for_term(term_code = product_code, chosen_language=chosen_language)

                for (nar_item, nar_name) in product_narrow_items:
                    dict_products[product_name].narrow_items.add(self.normalize_name(nar_name))
                    
        return dict_products

    def merge_products(self, dict_products):
        dict_list = sorted(list(dict_products.values()), key = lambda x: x.term_code)
        for i in range(len(dict_list)):
            for j in range(len(dict_list)):
                if i!= j and (self.calculate_jaccard(dict_list[i].narrow_items, dict_list[j].narrow_items) >= 0.5 or 
                               utils.normalized_levenshtein_score(dict_list[i].broad_name, dict_list[j].broad_name) >= 0.8):
                    new_set = self.merge_two_sets(dict_list[i].narrow_items, dict_list[j].narrow_items)
                    dict_list[i] = TermInfo(dict_list[i].broad_name, dict_list[i].term_code,new_set, dict_list[i].parent_name)
                    dict_list[j] = TermInfo(dict_list[j].broad_name, dict_list[j].term_code, set(), dict_list[j].parent_name)
        return dict_list

    def find_for_group_level_2(self, group_level_2_terms, chosen_language="en"):
        common_dict = {}
        for group_level_2 in group_level_2_terms:
            level_2_narrow_items = self.get_narrow_items_for_term(term_name = group_level_2, chosen_language=chosen_language)
            narrow_items = self.get_narrow_items_level_2(level_2_narrow_items, chosen_language=chosen_language)
            dict_products = self.find_narrow_items_level_4(narrow_items, chosen_language=chosen_language)
            common_dict[group_level_2] = self.merge_products(dict_products)
        return common_dict

    def get_mappings_for_2_level_terms(self, group_level_terms, chosen_languages="en", file_folder="../data"):
        for group_level in group_level_terms:
            dict_ready = []
            for lang in chosen_languages.split(","):
                common_dict = self.find_for_group_level_2([group_level], chosen_language=lang)
                for key, terms in common_dict.items():
                    for term in terms:
                        for narrow_item in term.narrow_items:
                            if narrow_item.strip() != "" and term.broad_name.strip() != "" and term.parent_name != "":
                                dict_ready.append((narrow_item, term.broad_name, term.parent_name))
            excel_writer.ExcelWriter().save_data_in_excel(
                dict_ready, ["narrow_name", "broad_name", "level_3_term"], "%s/map_%s.xlsx"%(
                    file_folder, group_level.replace(" ", "_")))
        return dict_ready
