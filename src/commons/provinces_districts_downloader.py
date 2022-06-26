import pycountry
from text_processing import text_normalizer
from utilities import excel_writer, utils

class ProvincesDistrictsDownloader:

    def __init__(self, path_to_gadm_shp="../tmp/gadm36_shp/gadm36.shp"):
        self.country_codes = self.create_countries_codes_map()
        self.freq_words = text_normalizer.get_all_freq_words()
        with shapefile.Reader(path_to_gadm_shp) as f:
            self.records = f.records()

    def get_country_name(self, key):
        country_name = ""
        try:
            country = pycountry.countries.get(alpha_2=key)
            if country != None:
                country_name = text_normalizer.normalize_country_name(country.name)
        except:
                print("Key " + key + " not found")
        return country_name

    def normalize_country_name(country_name):
        mapping = {"Aland":"Aland Islands",  "Brunei":"Brunei Darussalam",\
             "Czech Republic":"Czechia", "Democratic Republic of the Congo":"Congo",
             "Laos":"Lao People's Democratic Republic",\
             "Republic of Congo":"Congo", "Russia":"Russian Federation",
             "Northern Cyprus":"Cyprus", "Palestina":"Palestine",\
              "Syria":"Syrian Arab Republic", "Vietnam":"Viet Nam"}
        norm_country = text_normalizer.normalize_country_name(country_name)
        if norm_country in mapping:
            return mapping[norm_country]
        return norm_country

    def create_countries_codes_map(self):
        country_codes = {}
        for country in pycountry.countries:
            norm_country = text_normalizer.normalize_country_name(country.name)
            if norm_country != "Korea":
                country_codes[norm_country] = country.alpha_2
        country_codes["North Korea"] = "KP"
        country_codes["South Korea"] = "KR"
        return country_codes

    def derive_provinces_dictionary():
        dict_with_provinces = {}
        for idx, record in enumerate(self.records):
            country = self.normalize_country_name(record[3])
            name = record[6]
            var_names = record[7].split("|")
            district_name = record[18]
            var_district_names = record[19].split("|")
            if name == '':
                continue
            for dist_name in list(filter(None, var_district_names + [district_name, name] + var_names)):
                dist_name = dist_name.split("(")[0].split("[")[0].split(",")[0].strip()
                if dist_name not in dict_with_provinces:
                    dict_with_provinces[dist_name] = {}
                if country not in dict_with_provinces[dist_name]:
                    dict_with_provinces[dist_name][country] = set()
                dict_with_provinces[dist_name][country].add(name)
        keys_to_delete = set()
        for key in dict_with_provinces:
                if len(dict_with_provinces[key]) > 1:
                    keys_to_delete.add(key)
        for key in keys_to_delete:
            del dict_with_provinces[key]
        dict_with_provinces = self.enrich_with_subdivisions_map(dict_with_provinces)
        return dict_with_provinces

    def is_word_to_be_filtered(self, word):
        filtration_words = ["universit", "north","south","east","west",
                            "centr", "middl", "asia", "europ", "union",
                            "enterpris", "cocoa","summit", "savann", "spring",
                            "district", "province", "coast", "upper","lower",
                            "atlantic"]
        if word.lower() in freq_words or word.lower() in text_normalizer.stopwords_all or text_normalizer.is_abbreviation(word):
            return True
        for w in text_normalizer.get_stemmed_words_inverted_index(word):
            is_filtered = False
            for filter_word in filtration_words:
                if filter_word in w.lower():
                    is_filtered = True
                    break
            if not is_filtered and not text_normalizer.is_abbreviation(w):
                return False
        return True

    def enrich_with_subdivisions_map(self, dict_with_provinces):
        subdivisions_map = list(pycountry.subdivisions)
        for subdivision in subdivisions_map:
            sub_name = subdivision.name.split("(")[0].split("[")[0].split("/")[0].split(",")[0].strip()
            country_name = self.get_country_name(subdivision.country_code)
            if sub_name not in dict_with_provinces:
                sub_broad_name = sub_name
                max_sim = 0.0
                for dist in self.dict_with_districts:
                    try:
                        for broad_name in dict_with_provinces[dist][country_name]:
                            max_sim_term = max(
                                utils.normalized_levenshtein_score(broad_name, sub_name),
                                utils.normalized_levenshtein_score(dist, sub_name))
                            if max_sim_term > 0.7 and max_sim_term > max_sim:
                                max_sim = max_sim_term
                                sub_broad_name = broad_name
                    except:
                        pass
                dict_with_provinces[sub_name] = {country_name: set([sub_broad_name])}
                if sub_broad_name not in dict_with_provinces:
                    dict_with_provinces[sub_broad_name] = {country: set([sub_broad_name])}
        return dict_with_provinces

    def derive_districts_dictionary():
        dict_with_districts = {}
        for idx, record in enumerate(self.records):
            country = self.normalize_country_name(record[3])
            name = record[6]
            var_names = record[7].split("|")
            district_name = record[18]
            var_district_names = record[19].split("|")
            if district_name == '':
                continue
            for dist_name in list(filter(None, var_district_names + [district_name])):
                dist_name = dist_name.split("(")[0].split("[")[0].split(",")[0].strip()
                if dist_name not in dict_with_districts:
                    dict_with_districts[dist_name] = {}
                if country not in dict_with_districts[dist_name]:
                    dict_with_districts[dist_name][country] = set()
                dict_with_districts[dist_name][country].add((district_name, name))
                
        keys_to_delete = set()
        for key in dict_with_districts:
                if len(dict_with_districts[key]) > 1:
                    keys_to_delete.add(key)
        for key in keys_to_delete:
            del dict_with_districts[key]
        return dict_with_districts

    def save_provinces_dictionary(self, filename="provinces.xlsx"):
        self.derive_provinces_dictionary()
        pairs_to_write = []
        for key in dict_with_provinces:
            for country in dict_with_provinces[key]:
                for dist_name in dict_with_provinces[key][country]:
                    if not self.is_word_to_be_filtered(key) and not self.is_word_to_be_filtered(dist_name):
                            if country in country_codes:
                                country_code = country_codes[country]
                            else:
                                continue
                            pairs_to_write.append((key, dist_name, country, country_code))
        excel_writer.ExcelWriter().save_data_in_excel(
            pairs_to_write, ["Keyword", "Province", "Country", "Country code"], filename)

    def save_districts_dictionary(self, filename="districts.xlsx"):
        pairs_to_write = []
        for key in self.dict_with_districts:
            for country in self.dict_with_districts[key]:
                for dist_name, prov_name in self.dict_with_districts[key][country]:
                    if not self.is_word_to_be_filtered(key) and not self.is_word_to_be_filtered(dist_name):
                        if country in country_codes:
                            country_code = country_codes[country]
                        else:
                            continue
                        pairs_to_write.append((key, dist_name, prov_name, country, country_code))
        excel_writer.ExcelWriter().save_data_in_excel(
            pairs_to_write, ["Keyword", "District", "Province", "Country", "Country code"], filename)

    def find_provinces_districts(self, filename_for_districts, filename_for_provinces):
        self.dict_with_districts = self.derive_districts_dictionary()
        self.dict_with_provinces = self.derive_provinces_dictionary()
        self.save_districts_dictionary(filename=filename_for_districts)
        self.save_provinces_dictionary(filename=filename_for_provinces)
