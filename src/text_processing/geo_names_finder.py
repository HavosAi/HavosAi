import spacy
from geotext import GeoText
import pycountry
from text_processing import text_normalizer
import pandas as pd
import re
from utilities import excel_reader
from text_processing import search_engine_insensitive_to_spelling
import pandas as pd
import langdetect

nlp = spacy.load('en_core_web_sm')

class GeoNameFinder:

    def __init__(self, geo_regions_file="../data/GeoRegions.xlsx",
                 world_bank_regions_file="../data/WorldBankCountriesDivision.xlsx",
                 provinces_file="../data/provinces.xlsx",
                 districts_file="../data/districts.xlsx",
                 additional_countries_file="../data/map_additional_country_names.xlsx",
                 additional_geo_regions_file="../data/map_additional_regions.xlsx",
                 country_adjectives_file="../data/map_country_adjectives.xlsx",
                 currencies_file="../data/map_currencies.xlsx",
                 country_groups_file="../data/map_country_groups.xlsx",
                 country_groups_income_level_file="../data/map_country_groups_income_level.xlsx"):
        self.geo_regions = {}
        self.world_bank_regions = {}
        self.region_by_name = {}
        self.countries_map = {}
        self.country_adjectives = {}
        self.currencies = {}
        self.country_groups = {}
        self.country_groups_income_level = {}
        self.initialize_geo_regions_map(geo_regions_file, additional_geo_regions_file)
        self.initialize_world_bank_regions_map(world_bank_regions_file)
        self.fill_countries(additional_countries_file)
        self.fill_dicts(country_adjectives_file, "Keyword", "Country_code", self.country_adjectives)
        self.fill_dicts(currencies_file, "Keyword", "Country_code", self.currencies)
        self.fill_dicts(country_groups_file, "Keyword", "Country_code", self.country_groups)
        self.fill_dicts(country_groups_income_level_file, "Keyword", "Region", self.country_groups_income_level)
        self.provinces = self.fill_provinces(provinces_file)
        self.districts =  self.fill_provinces(districts_file)

    def fill_provinces(self, filename):
        map_df = excel_reader.ExcelReader().read_df_from_excel(filename)
        provinces = {}
        for i in range(len(map_df)):
            if map_df.values[i][-1].strip() == '':
                map_df.values[i][-1] = "NA"
            key_word = map_df["Keyword"].values[i].strip()
            res = tuple(map_df.values[i][1:])
            provinces[key_word] = res
            if self.normalize_geo_name(key_word) != "":
                provinces[self.normalize_geo_name(key_word)] = res
            if self.normalize_geo_name(key_word, filter_names = True) != "":
                provinces[self.normalize_geo_name(key_word, filter_names = True)] = res
        return provinces

    def fill_dicts(self, filename, keyword_column, country_code_column, dict_to_fill, to_lower=False):
        if not filename:
            return
        map_df = excel_reader.ExcelReader().read_df_from_excel(filename)
        for i in range(len(map_df)):
            keyword = map_df[keyword_column].values[i].strip()
            if to_lower:
                keyword = keyword.lower()
            if keyword not in dict_to_fill:
                dict_to_fill[keyword] = []
            dict_to_fill[keyword].append(
                (map_df[country_code_column].values[i].strip() if map_df[country_code_column].values[i].strip() else "NA"))

    def fill_countries(self, additional_countries_file):
        for country in list(pycountry.countries):
            country_name_normalized = text_normalizer.normalize_country_name(country.name).lower()
            if country_name_normalized not in self.countries_map:
                self.countries_map[country_name_normalized] = []
            self.countries_map[country_name_normalized].append(country.alpha_2)
        self.fill_dicts(additional_countries_file, "Country", "Country_code", self.countries_map, to_lower=True)

    def contain_filter_words(self, word):
        for filter_word in ["universit", "north","south","east","west", "centr", "middl", "asia", "europ", "union", \
                            "enterpris", "cocoa","summit", "savann", "spring"]:
            if filter_word in word:
                return True
        return False

    def word_to_camel_case(self, word):
        if word == word.upper():
            return word[0] + word[1:].lower()
        return word

    def get_transformed_words(self, word_expression):
        words = [self.word_to_camel_case(word) for word in word_expression.split() if not self.contain_filter_words(word.lower())];
        transformed_expressions = [" ".join(words)]
        return transformed_expressions

    def contains_usa_name(self, transformed_word):
        return re.search(r"\busa\b", transformed_word.lower()) != None or re.search(r"\bunited states\b", transformed_word.lower())!= None or re.search(r"\bUS(?!((\s*\$)|(\s*dollar)))", transformed_word)!= None 

    def contains_uk_name(self, transformed_word):
        pattern_uk_names = ["uk", "england", "scotland", "wales", "nothern ireland"]
        for pattern in pattern_uk_names:
            if re.search(r"\b%s\b"%pattern, transformed_word.lower()) != None:
                return True
        return False

    def normalize_geo_name(self, geo_name, filter_names = False):
        words_to_remove = ["basin", "valley", "city", "town", "province", "district", "d'oeste", "local",\
                          "government", "area", "county", "region", "village", "state", "republic", "protected",\
                           "zone","oblast'", "municipality","prefecture","sub-county", "island","okrug","avtonomnyy",\
                          "avtonomnaya", "kray", "voblasc'", "horad", "županija","territory","novads","Apskritis",\
                          "oblysy", "kanton"]
        word_expr = " ".join([w for w in geo_name.split(",")[0].split(" ") \
                              if w.lower() not in text_normalizer.stopwords_all \
                             and not text_normalizer.is_abbreviation(w)]).strip()
        if filter_names:
            word_expr = " ".join([w for w in word_expr.split(" ") \
                              if w.lower() not in words_to_remove]).strip()
        return word_expr

    def get_country_names_and_codes(self, codes_set):
        country_codes = set()
        countries = set()
        for code in codes_set:
            if code == 'UK':
                code = 'GB'
            country_name = self.get_country_name(code)
            if country_name != "":
                countries.add(country_name)
                country_codes.add(code)
        return countries, country_codes

    def get_country_name(self, key):
        country_name = ""
        try:
            country = pycountry.countries.get(alpha_2=key)
            if country != None:
                country_name = text_normalizer.normalize_country_name(country.name)
        except:
                print("Key " + key + " not found")
        return country_name

    def find_geo_name_info(self, dictionary, text):
        if text in dictionary:
            return dictionary[text]
        if self.normalize_geo_name(text) in dictionary:
            return dictionary[self.normalize_geo_name(text)]
        if self.normalize_geo_name(text, filter_names = True) in  dictionary:
            return dictionary[self.normalize_geo_name(text, filter_names = True)]
        return None

    def add_country_code(self, country_codes, code, only_countries):
        if len(only_countries) == 0:
            country_codes.add(code)
        elif code in only_countries:
            country_codes.add(code)
        return country_codes

    def get_country_mentions_without_nationalities(self, text):
        nationalities = GeoText(text).nationalities
        for nationality in nationalities:
            text = re.sub(r"\b%s\b"%nationality, " ", text)
        return GeoText(text).country_mentions

    def get_countries_from_text(self, text, only_countries = []):
        doc = nlp(text)
        lang_text = "en"
        try:
            lang_text = langdetect.detect(text)
        except:
            pass
        allowed_tag_names = ['GPE', 'LOC', 'ORG']
        ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents if e.label_ in  allowed_tag_names]
        country_codes = set()
        provinces = set()
        districts = set()
        country_codes_by_provinces = set()
        words_allowed = {"Como": "en", "Banks": "", "Latina": "en", "Southern Region": "", "United Kingdom": "",
                        "Nord-Est": "", "Nord": "", "La Argentina": "", "Oriental": "",
                        "Water Island": "", "University City": "", "Highlands": "",
                        "La Labor": "en", "Western Urban": "", "Citrus": "", "Buffalo": "",
                        "Para": "en", "Banco": "en", "El Banco": "en", "An Lão": "",
                        "An Lao": "", "Lao": ""}
        for word in ents:
            country_codes_to_add = set()
            for transformed_word in self.get_transformed_words(word[0]):
                if len(self.get_country_mentions_without_nationalities(transformed_word)) > 0:
                    for key, number in self.get_country_mentions_without_nationalities(transformed_word).items():
                        country_codes_to_add = self.add_country_code(country_codes_to_add, key, only_countries)
                if self.contains_usa_name(transformed_word):
                    country_codes_to_add = self.add_country_code(country_codes_to_add, 'US', only_countries)

            province_info = self.find_geo_name_info(self.provinces, word[0])
            district_info = self.find_geo_name_info(self.districts, word[0])
            if (province_info is not None and province_info[0].lower() in self.countries_map) or\
                    (province_info is not None and province_info[0] in words_allowed and words_allowed[province_info[0]] != lang_text):
                country_codes = country_codes.union(country_codes_to_add - set([province_info[2]]))
                continue
            if (district_info is not None and district_info[0].lower() in self.countries_map) or\
                    (district_info is not None and district_info[0] in words_allowed and words_allowed[district_info[0]] != lang_text):
                country_codes = country_codes.union(country_codes_to_add - set([district_info[3]]))
                continue

            if province_info is not None and (len(only_countries) == 0 or province_info[2] in only_countries):
                provinces.add("%s/%s"%(province_info[1], province_info[0]))
                country_codes_by_provinces.add(province_info[2])
            
            if district_info is not None and (len(only_countries) == 0 or district_info[3] in only_countries):
                districts.add("%s/%s/%s"%(district_info[2], district_info[1], district_info[0]))
                country_codes_by_provinces.add(district_info[3])
            country_codes = country_codes.union(country_codes_to_add)
                
        country_codes = country_codes.intersection(set(self.get_country_mentions_without_nationalities(self.get_transformed_words(text)[0]).keys()))
        if self.contains_usa_name(text):
            country_codes = self.add_country_code(country_codes, 'US', only_countries)
        if self.contains_uk_name(text):
            country_codes = self.add_country_code(country_codes, 'GB', only_countries)
        if len(only_countries) > 0:
            country_codes = country_codes.intersection(set(only_countries))

        country_codes = country_codes.union(country_codes_by_provinces)
        country_names, country_codes = self.get_country_names_and_codes(country_codes)
        return country_names, country_codes, provinces, districts

    def get_all_countries_from_text(self, text, only_countries = []):
        countries_all, country_codes_all, provinces_all, districts_all = [],[],[],[]
        countries, country_codes, provinces, districts = self.get_countries_from_text(text, only_countries = only_countries)
        countries_without_accented_chars, country_codes_without_accented_chars,\
        provinces_acc, districts_acc = self.get_countries_from_text(
            text_normalizer.remove_accented_chars(text), only_countries = only_countries)
        countries_all.extend(list(countries.union(countries_without_accented_chars)))
        country_codes_all.extend(list(country_codes.union(country_codes_without_accented_chars)))
        provinces_all.extend(list(provinces.union(provinces_acc)))
        districts_all.extend(list(districts.union(districts_acc)))
        return list(set(countries_all)), list(set(country_codes_all)),\
         list(set(provinces_all)), list(set(districts_all))

    def initialize_geo_regions_map(self, geo_regions_file, additional_geo_regions_file):
        map_df = excel_reader.ExcelReader().read_df_from_excel(geo_regions_file)
        for i in range(len(map_df)):
            country_name = text_normalizer.remove_accented_chars(map_df["Country"].values[i].strip())
            region_name = text_normalizer.remove_accented_chars(map_df["Region"].values[i].strip())
            self.geo_regions[country_name] = region_name
            region_parts = region_name.split(" and ")
            for region_part in region_parts:
                if region_part not in self.region_by_name:
                    self.region_by_name[region_part] = region_name
        if additional_geo_regions_file.strip():
            map_df = excel_reader.ExcelReader().read_df_from_excel(additional_geo_regions_file)
            for i in range(len(map_df)):
                region_keyword = text_normalizer.remove_accented_chars(map_df["Region_keyword"].values[i].strip())
                region_name = text_normalizer.remove_accented_chars(map_df["Region"].values[i].strip())
                self.region_by_name[region_keyword] = region_name
            
    def initialize_world_bank_regions_map(self, world_bank_regions_file):
        map_df = excel_reader.ExcelReader().read_df_from_excel(world_bank_regions_file)
        for i in range(len(map_df)):
            country_name = text_normalizer.remove_accented_chars(map_df["Country"].values[i].strip())
            if not country_name in self.world_bank_regions:
                self.world_bank_regions[country_name] = []
            self.world_bank_regions[country_name].append(text_normalizer.remove_accented_chars(map_df["Region"].values[i].strip()))

    def fill_countries_by_search(self, articles_df, search_engine_inverted_index, prefix_for_columns=""):
        country_codes_column = prefix_for_columns + "country_codes"
        countries_mentioned_column = prefix_for_columns + "countries_mentioned"
        for country_code in self.countries_map_by_articles:
            for article in self.countries_map_by_articles[country_code]:
                if country_code not in articles_df[country_codes_column].values[article]:
                    articles_df[country_codes_column].values[article].append(country_code)
                    articles_df[countries_mentioned_column].values[article].append(
                        self.get_country_name(country_code))
        return articles_df

    def get_countries_by_search(self, text):
        small_search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(load_abbreviations = False, columns_to_process = ["text"])
        small_search_engine_inverted_index.create_inverted_index(pd.DataFrame([text],columns = ["text"]), print_info  = False)
        country_codes = set()
        for country in self.countries_map:
            for article in small_search_engine_inverted_index.find_articles_with_keywords([country],0.92,extend_with_abbreviations = False):
                country_codes = country_codes.update(self.countries_map[country])
        return country_codes

    def create_countries_map_by_articles(self, search_engine_inverted_index):
        self.countries_map_by_articles = {}
        for country in self.countries_map:
            articles = search_engine_inverted_index.find_articles_with_keywords(
                [country], 0.92, extend_with_abbreviations = False)
            for country_code in self.countries_map[country]:
                self.countries_map_by_articles[country_code] = articles

    def fill_regions_by_countries(self, articles_df, prefix_for_columns=""):
        articles_df[prefix_for_columns+"geo_regions"] = ""
        articles_df[prefix_for_columns+"world_bankdivision_regions"] = ""
        for i in range(len(articles_df)):
            articles_df[prefix_for_columns+"geo_regions"].values[i] = []
            articles_df[prefix_for_columns+"world_bankdivision_regions"].values[i] = []
            for country in articles_df[prefix_for_columns+"countries_mentioned"].values[i]:        
                if country in self.geo_regions:
                    articles_df[prefix_for_columns+"geo_regions"].values[i].append(self.geo_regions[country])
                if country in self.world_bank_regions:
                    articles_df[prefix_for_columns+"world_bankdivision_regions"].values[i].extend(self.world_bank_regions[country])
            articles_df[prefix_for_columns+"geo_regions"].values[i] = list(set(articles_df[prefix_for_columns+"geo_regions"].values[i]))
            articles_df[prefix_for_columns+"world_bankdivision_regions"].values[i] = list(
                set(articles_df[prefix_for_columns+"world_bankdivision_regions"].values[i]))
        return articles_df

    def fill_regions_from_search(self, articles_df,search_engine_inverted_index,prefix_for_columns=""):
        for region in self.region_by_name:
            for article in search_engine_inverted_index.find_articles_with_keywords([region.lower().strip()], 0.92, extend_with_abbreviations = False):
                if self.region_by_name[region] not in articles_df[prefix_for_columns+"geo_regions"].values[article]:
                    articles_df[prefix_for_columns+"geo_regions"].values[article].append(self.region_by_name[region])
        return articles_df

    def fill_by_search(self, articles_df, search_engine_inverted_index, filling_dict, prefix_for_columns=""):
        country_codes_column = prefix_for_columns + "country_codes"
        countries_mentioned_column = prefix_for_columns + "countries_mentioned"
        for keyword in filling_dict:
            for article in search_engine_inverted_index.find_articles_with_keywords([keyword], 0.92, extend_with_abbreviations = False):
                if articles_df[country_codes_column].values[article]:
                    continue
                for country_code in filling_dict[keyword]:
                    if country_code not in articles_df[country_codes_column].values[article]:
                        articles_df[country_codes_column].values[article].append(country_code)
                        articles_df[countries_mentioned_column].values[article].append(
                            self.get_country_name(country_code))
        return articles_df

    def fill_by_search_country_groups(self, articles_df, search_engine_inverted_index, prefix_for_columns=""):
        country_codes_column = prefix_for_columns + "country_codes"
        countries_mentioned_column = prefix_for_columns + "countries_mentioned"
        country_groups_column = prefix_for_columns + "country_groups"
        countries_indicators = ["country", "region", "member", "state", "district", "area", "representative"]
        already_used_articles_with_country_groups = set()
        for keyword in self.country_groups:
            for country_indicator in countries_indicators:
                for article in search_engine_inverted_index.find_articles_with_keywords([keyword + " " + country_indicator], 0.92, extend_with_abbreviations = False):
                    if keyword not in articles_df[country_groups_column].values[article]:
                        articles_df[country_groups_column].values[article].append(keyword)
                    if articles_df[country_codes_column].values[article] and article not in already_used_articles_with_country_groups:
                        continue
                    for country_code in self.country_groups[keyword]:
                        if country_code not in articles_df[country_codes_column].values[article]:
                            articles_df[country_codes_column].values[article].append(country_code)
                            articles_df[countries_mentioned_column].values[article].append(
                                self.get_country_name(country_code))
                            already_used_articles_with_country_groups.add(article)
        for keyword in self.country_groups_income_level:
            for article in search_engine_inverted_index.find_articles_with_keywords([keyword], 0.92, extend_with_abbreviations = False):
                if keyword not in articles_df[country_groups_column].values[article]:
                    articles_df[country_groups_column].values[article].append(keyword)
        return articles_df

    def fill_regions_by_country_groups(self, articles_df, search_engine_inverted_index, prefix_for_columns=""):
        world_bank_groups_column = prefix_for_columns+"world_bankdivision_regions"
        if world_bank_groups_column not in articles_df.columns:
            articles_df[world_bank_groups_column] = ""
        for i in range(len(articles_df)):
            if articles_df[world_bank_groups_column].values[i] == "":
                articles_df[world_bank_groups_column].values[i] = []
            for country_group in articles_df[prefix_for_columns+"country_groups"].values[i]:        
                if country_group in self.country_groups_income_level:
                    articles_df[world_bank_groups_column].values[i].extend(self.country_groups_income_level[country_group])
            articles_df[world_bank_groups_column].values[i] = list(set(articles_df[world_bank_groups_column].values[i]))
        return articles_df


    def find_countries_and_regions_from_search(self, articles_df, search_engine_inverted_index, prefix_for_columns="",
                check_only_country_names_and_divisions=False):
        articles_df = self.fill_countries_by_search(articles_df, search_engine_inverted_index, prefix_for_columns=prefix_for_columns)
        if not check_only_country_names_and_divisions:
            articles_df = self.fill_by_search(articles_df, search_engine_inverted_index, self.country_adjectives, prefix_for_columns=prefix_for_columns)
        if not check_only_country_names_and_divisions:
            articles_df = self.fill_by_search(articles_df, search_engine_inverted_index, self.currencies, prefix_for_columns=prefix_for_columns)
        articles_df = self.fill_by_search_country_groups(articles_df, search_engine_inverted_index, prefix_for_columns=prefix_for_columns)
        articles_df = self.fill_regions_by_countries(articles_df,prefix_for_columns=prefix_for_columns)
        articles_df = self.fill_regions_from_search(articles_df,search_engine_inverted_index,prefix_for_columns=prefix_for_columns)
        articles_df = self.fill_regions_by_country_groups(articles_df,search_engine_inverted_index,prefix_for_columns=prefix_for_columns)
        return articles_df

    def extract_country_by_geotext(self, raw_university_name):
        raw_university_name = raw_university_name.replace("University", " ")
        countries = GeoText(raw_university_name).country_mentions
        country_code = ""
        for country in countries:
            if country != "US" and country != "XK":
                if country == "UK":
                    country = "GB"
                country_code = country
                break
        return "" if country_code == "" else self.get_country_name(country_code)

    def get_country_from_text_with_spacy(self, text):
        doc = nlp(text)
        ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents if e.label_ in  ['GPE','LOC','ORG','NORP']]
        for word in ents:
            country = self.extract_country_by_geotext(word[0])
            if country != "":
                return country
        return ""

    def get_country_from_raw_text(self, raw_text):
        country = self.extract_country_by_geotext(raw_text)
        if country == "":
            return self.get_country_from_text_with_spacy(raw_text)
        return country

    def get_country_from_text_with_and_without_accented_chars(self, raw_text):
        country_with_accented_chars = self.get_country_from_raw_text(raw_text)
        country_without_accented_chars = self.get_country_from_raw_text(text_normalizer.remove_accented_chars(raw_text))
        return text_normalizer.remove_accented_chars(country_with_accented_chars if country_with_accented_chars != "" else country_without_accented_chars)

    def extract_city_name_with_spacy(self, raw_university_name):
        doc = nlp(raw_university_name)
        ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents if e.label_ in  ['GPE','LOC','ORG','NORP']]
        for word in ents:
            city = self.extract_city_name_with_geotext(word[0])
            if city != "":
                return city
        return ""

    def extract_city_name_with_geotext(self, raw_university_name):
        city_name = ""
        if raw_university_name != "":
            city_names = [city for city in GeoText(raw_university_name).cities if "Univer" not in city]
            city_name = "" if len(city_names) == 0 else city_names[-1].lower()
        return city_name

    def extract_city_name(self, raw_university_name):
        city = self.extract_city_name_with_geotext(raw_university_name)
        if city == "":
            return self.extract_city_name_with_spacy(raw_university_name)
        return city 

    def get_city_from_text_with_and_without_accented_chars(self, raw_text):
        city_with_accented_chars = self.extract_city_name(raw_text)
        city_without_accented_chars = self.extract_city_name(text_normalizer.remove_accented_chars(raw_text))
        return text_normalizer.remove_accented_chars(city_with_accented_chars if city_with_accented_chars != "" else city_without_accented_chars)

    def label_articles_with_geo_names(self, articles_df, search_engine_inverted_index,
        continue_label = False, only_countries_columns = [], columns_with_country_code=[], use_cache=False,
        columns_to_process=["abstract", "title", "keywords", "identificators", "sentence"], prefix_for_columns="",
        check_only_country_names_and_divisions=False):
        for column in ["countries_mentioned", "country_codes","provinces", "districts", "country_groups"]:
            column = prefix_for_columns + column
            if column not in articles_df.columns or not continue_label:
                articles_df[column] = ""
        self.create_countries_map_by_articles(search_engine_inverted_index)
        geo_names_cache = {}
        for i in range(len(articles_df)):
            countries_mentioned_column = prefix_for_columns + "countries_mentioned"
            country_codes_column = prefix_for_columns + "country_codes"
            provinces_column = prefix_for_columns + "provinces"
            districts_column = prefix_for_columns + "districts"
            country_groups_column = prefix_for_columns + "country_groups"
            if articles_df[countries_mentioned_column].values[i] != "" and (articles_df[countries_mentioned_column].values[i] == articles_df[countries_mentioned_column].values[i]):
                continue
            only_countries = set()
            if len(columns_with_country_code) > 0:
                for column in columns_with_country_code:
                    if type(articles_df[column].values[i]) == str:
                        only_countries.add(articles_df[column].values[i])
                    if type(articles_df[column].values[i]) == list:
                        only_countries = only_countries.union(set(articles_df[column].values[i]))
            else:
                only_countries_text = " . ".join([articles_df[column].values[i] for column in only_countries_columns])
                only_countries = list(set(self.get_all_countries_from_text(only_countries_text)[1]).\
                    union(self.get_countries_by_search(only_countries_text)))
            full_text = " . ".join([articles_df[column].values[i] for column in columns_to_process if column in articles_df.columns])
            if use_cache and full_text in geo_names_cache:
                countries, country_codes, provinces, districts = geo_names_cache[full_text]
            else:
                countries, country_codes, provinces, districts =  self.get_all_countries_from_text(full_text,
                    only_countries = only_countries)
                if use_cache:
                    geo_names_cache[full_text] = (countries, country_codes, provinces, districts)
            articles_df[countries_mentioned_column].values[i] = countries
            articles_df[country_codes_column].values[i] = country_codes
            articles_df[provinces_column].values[i] = provinces
            articles_df[districts_column].values[i] = districts
            articles_df[country_groups_column].values[i] = []
            #print(only_countries, articles_df["countries_mentioned"].values[i], articles_df["country_codes"].values[i],
            #    articles_df["provinces"].values[i], articles_df["districts"].values[i])
            if i%5000 == 0 or i == len(articles_df) -1:
                print("Processed %d items" % i)
        articles_df = self.find_countries_and_regions_from_search(articles_df, search_engine_inverted_index, prefix_for_columns=prefix_for_columns,
            check_only_country_names_and_divisions=check_only_country_names_and_divisions)
        for column in ["country_codes", "countries_mentioned","geo_regions", "world_bankdivision_regions", "provinces", "districts", "country_groups"]:
            column = prefix_for_columns + column
            articles_df = text_normalizer.replace_string_default_values(articles_df, column)
            for i in range(len(articles_df)):
                articles_df[column].values[i] = list(set(articles_df[column].values[i]))
        return articles_df