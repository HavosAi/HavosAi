import pandas as pd
import os
import math
import fnmatch
import re
from text_processing import text_normalizer
from dateutil.parser import parse
from utilities import excel_reader

class DataPreparationBase:

    def __init__(self):
        self.dataset_names_full = { "web":"Web of Science",  "econ":"Econlit", "cab":"CAB", "econlit":"Econlit",\
                      "pqdissertationtheses":"Proquest", "wdr":"WDR2008", "clrtb":"CLRTB_PHL", "scopus":"Scopus"}
        self.datasets_science_journals = ["Scopus", "CAB", "Econlit", "Proquest", "Web of Science", "Agricola","ISI", "CABI","African","CLRTB_PHL"]
        self.load_dataset_mappings()

    def load_dataset_mappings(self):
        dfs = pd.read_excel("../data/Dataset_mappings.xlsx", sheet_name = None)
        self.dataset_mappings = {}
        for key in dfs:
            self.dataset_mappings[key] = {}
            for i in range(len(dfs[key])):
                self.dataset_mappings[key][dfs[key]['External column name'].values[i]] =\
                (dfs[key]['Our column name'].values[i], dfs[key]['Priority'].values[i])

    def prepare_mapping_for_dataset(self, dataset_name, fields):
        mapping = {}
        if dataset_name in self.dataset_mappings:
            mapping = self.dataset_mappings[dataset_name]
        else:
            mapping = self.dataset_mappings["Default"]
        new_mapping = {}
        for field in fields:
            if field in mapping:
                our_column_name = mapping[field][0]
                if our_column_name not in new_mapping:
                    new_mapping[our_column_name] = []
                new_mapping[our_column_name].append((field, mapping[field][1]))
        full_mapping = {}
        for key in new_mapping:
            if len(new_mapping[key]) == 1:
                full_mapping[new_mapping[key][0][0]] = key
            else:
                sorted_list = sorted(new_mapping[key])
                full_mapping[sorted_list[0][0]] = key
        return full_mapping

    def find_year(self, year_val):
        if type(year_val) == str:
            if len(year_val) > 0 and year_val[0] == "=":
                year_val = year_val[2:-1]
            if year_val.strip() == "":
                year_val = 2018
            else:
                year_val = parse(year_val).year
        else:
            if year_val == 0:
                year_val = 2018
            if math.log(year_val,10) >= 4:
                year_val = int(str(year_val)[:4])
        return year_val

    def create_link(self, url):
        if url == "":
            return ""
        if url.strip().startswith("https:") or url.strip().startswith("http:"): 
            return url.strip()
        return "https://doi.org/" + url

    def fill_required_fields(self, df, dataset_name):
        highly_required_fields = ["title","abstract","AU","year"]
        for key in highly_required_fields:
            if key not in df.columns:
                print("Column %s was not found"%key)
        required_fields = ["keywords","identificators","email","journal","raw_affiliation","url","publisher","abstract"]
        for field in required_fields:
            if field not in df.columns:
                df[field] = ""
        return df

    def fill_common_fields(self, df, dataset_name):
        df = self.fill_dataset_type(df)
        for i in range(len(df)):
            df["title"].values[i] = df["title"].values[i].strip()
            df["year"].values[i] = self.find_year(df["year"].values[i])
        df = df[df["title"] != ""]
        df = df[df["year"] != 0]
        return df

    def prepare_dataset(self, filename, dataset_name, year_to_filter = None):
        df = excel_reader.ExcelReader().read_file(filename)
        mapping = self.prepare_mapping_for_dataset(dataset_name, df.columns)
        df = df.rename(mapping, axis=1)
        df["dataset"] = dataset_name
        df = self.fill_required_fields(df, dataset_name)
        df = self.process_additional_datasets(df, dataset_name)
        if dataset_name in ["Scopus"]:
            for i in range(len(df)):
                df["AU"].values[i] = df["AU"].values[i].replace(",",";")
            for cor_address_i in range(len(df['email'].values)):
                splitted_cor_address = df['email'].values[cor_address_i].split('email:')
                if len(splitted_cor_address) > 1:
                    df['email'].values[cor_address_i] = splitted_cor_address[1].strip()
                else:
                    df['email'].values[cor_address_i] = ""
            df = text_normalizer.update_title_and_abstract_only_english(df, ".", "[")
        if dataset_name in ["ISI"]:
            df = text_normalizer.update_title_and_abstract_only_english(df, "RESUME", ";")
            df = text_normalizer.update_title_and_abstract_only_english(df, ".", ".")
        if dataset_name in ["CABI","African","Web of Science"]:
            df = text_normalizer.update_title_and_abstract_only_english(df)
        if dataset_name in ["CLRTB_PHL"]:
            for i in range(len(df)):
                if "Author Affiliation:" in df["raw_affiliation"].values[i] and "Author Email:" in df["raw_affiliation"].values[i]:
                    df["email"].values[i] = df["raw_affiliation"].values[i].split("Author Email:")[1]
                    df["raw_affiliation"].values[i] = df["raw_affiliation"].values[i].split("Author Email:")[0].split("Author Affiliation:")[1]
            for i in range(len(df)):
                if df["Comment"].values[i] != df["Comment"].values[i]:
                    df["Comment"].values[i] = ''
                if df["Comment as to why"].values[i] != df["Comment as to why"].values[i]:
                    df["Comment as to why"].values[i] = ''
            df["Comments"] = df["Comment"] + " " + df["Comment as to why"]
        for i in range(len(df)):
            df["url"].values[i] = self.create_link(df["url"].values[i])
        if dataset_name in ["Econlit"]:
            for i in range(len(df)):
                new_keywords = []
                for keyword in df["keywords"].values[i].split(";"):
                    new_keywords.append(re.sub(r"\b[A-Z]\d{2}\b","",keyword).strip())
                df["keywords"].values[i] = ";".join(new_keywords)
        if dataset_name in ["Proquest"]:
            for i in range(len(df)):
                new_keywords = []
                for keyword in df["keywords"].values[i].split(";"):
                    key_w = keyword.split(":")[1].strip() if len(keyword.split(":"))> 1 else keyword.strip()
                    if key_w.startswith("(UMI)") or key_w.startswith("http") or key_w.startswith("No ") or key_w.startswith("//"):
                        continue
                    new_keywords.append(key_w)
                df["keywords"].values[i] = ";".join(new_keywords)
        df = self.fill_common_fields(df, dataset_name)
        if year_to_filter != None:
            df = df[df["year"]>=year_to_filter]
        return df[["AU","title","year","journal","abstract","url","raw_affiliation", "keywords", "email","identificators","dataset","publisher","dataset_type"]]

    def process_additional_datasets(self, df, dataset_name):
        if "year" not in df.columns and dataset_name in ["Agricola"]:
            df["year"] = ""
            for i in range(len(df)):
                year = re.search(r"\b\d{4}\b", df["journal"].values[i])
                df["year"].values[i] = int(year.group(0)) if year != None else 0
                df["journal"].values[i] = df["journal"].values[i].split(".")[0]
                df["journal"].values[i] = re.sub("\[\w.?\]","",df["journal"].values[i])
                df["AU"].values[i] = df["AU"].values[i].replace("\n",";")
                df["keywords"].values[i] = df["MH"].values[i].replace("\n",";") + ";" + df["DE"].values[i].replace("\n",";") +\
                df["ID"].values[i].replace("\n",";")
                df["url"].values[i] = df["url"].values[i].split("Available")[0]
                df["raw_affiliation"].values[i] = df["raw_affiliation"].values[i].replace("\n",";")
        if dataset_name in ["CAB"]:
            if "VN" in df.columns and df["VN"].values[0] == "Ovid Technologies":
                if "year" not in df.columns:
                    df["year"] = df["UI"]
                for i in range(len(df)):
                    df["journal"].values[i] = df["journal"].values[i].split(";")[0]
                    df["AU"].values[i] = df["AU"].values[i].replace("\n",";")
                    df["keywords"].values[i] = df["MH"].values[i].replace("\n",";") + ";" + df["BT"].values[i].replace("\n",";") +";"+\
                    (df["ID"].values[i].replace("\n",";") if "ID" in df.columns else "") + ";" + (df["CP"].values[i].replace("\n",";") if "CP" in df.columns else "") 
                    if "url" in df.columns:
                        df["url"].values[i] = df["url"].values[i].split("Available")[0]
        return df

    def fill_dataset_type(self, df):
        df["dataset_type"] = ""
        for i in range(len(df)):
            if df["dataset"].values[i] in self.datasets_science_journals:
                df["dataset_type"].values[i] = "Science Journals"
            else:
                df["dataset_type"].values[i] = "Grey Literature"
        return df

    def process_teams_folder(self, folder, team_name):
        full_df = pd.DataFrame()
        for filename in os.listdir(folder):
            dataset_name = re.search("[^\d\s_.]+",filename)
            if dataset_name != None:
                dataset_name = dataset_name.group(0)
            if dataset_name.lower() in self.dataset_names_full:
                dataset_name = self.dataset_names_full[dataset_name.lower()]
            if dataset_name not in self.dataset_mappings:
                print("filename %s from unknown source"%filename)
            df = self.prepare_dataset(os.path.join(folder,filename), dataset_name)
            if len(df) > 0:
                print("dataset %s is processed"%dataset_name)
                print(len(df))
                df["team_tags"] = ""
                for i in range(len(df)):
                    df["team_tags"].values[i] = [team_name]
                full_df = pd.concat([full_df, df], sort=False)
        return full_df

    def process_folder_with_files(self, folder):
        full_df = pd.DataFrame()
        for filename in os.listdir(folder):
            dataset_name = re.search("[^\d\s_.]+",filename)
            if dataset_name != None:
                dataset_name = dataset_name.group(0)
            if dataset_name != None and dataset_name.lower() in self.dataset_names_full:
                dataset_name = self.dataset_names_full[dataset_name.lower()]
                df = self.prepare_dataset(os.path.join(folder,filename), dataset_name)
            else:
                dataset_name = None
                df = self.process_unique_dataset(os.path.join(folder,filename))
            if len(df) > 0:
                print("dataset %s is processed"%(dataset_name if dataset_name is not None else filename))
                print(len(df))
                full_df = pd.concat([full_df, df], sort=False)
        return full_df

    def process_unique_sources(self, team_num, team_name):
        full_df = pd.DataFrame()
        for filename in os.listdir("../tmp/%d"%team_num):
            if filename[-5:] == ".xlsx" or filename[-4:] == ".csv":
                df = self.process_unique_dataset(os.path.join("../tmp/%d"%team_num, filename))
                if len(df) > 0:
                    print("dataset %s is processed"%df["dataset"].values[0])
                    print(len(df))
                    df["team_tags"] = ""
                    for i in range(len(df)):
                        df["team_tags"].values[i] = [team_name]
                    full_df = pd.concat([full_df, df], sort=False)
        return full_df

    def process_unique_dataset(self, filename, year_to_filter = None):
        df = excel_reader.ExcelReader().read_file(filename)
        dataset_name = df["dataset_name"].values[0] if "dataset_name" in df.columns else df["source_name"].values[0]
        print(dataset_name)
        if dataset_name in ["IZA"]:
            for i in range(len(df)):
                df["title"].values[i] = ":".join(df["title"].values[i].split(":")[1:]) if len(df["title"].values[i].split(":")) > 1 else df["title"].values[i]
                df["authors"].values[i] = df["authors"].values[i].replace(",",";")
                df["keywords"].values[i] = df["keywords"].values[i].replace(",",";")
                df["abstract"].values[i] = text_normalizer.clean_text_from_commas(df["abstract"].values[i])
            df = df.rename({"authors":"AU","file_urls":"url", "dataset_name":"dataset"},axis=1)
        if dataset_name in ["Gardian"]:
            df["year"] = ""
            for i in range(len(df)):
                year = re.search("\d{4}", df["citation"].values[i])
                df["year"].values[i] = int(year.group(0)) if year != None else 2018
            df = df.rename({"authors":"AU","dataset_name":"dataset", "publication":"journal", "abstract_link":"url"},axis=1)
        if dataset_name in ["Cochrane","ICAR","Greenwich"]:
            df = df.rename({"Author":"AU","dataset_name":"dataset", "Publication Title":"journal", "abstract_link":"url",\
                           "Publication Year":"year", "Title":"title", "Url":"url", "Abstract Note":"abstract", "Manual Tags":"keywords",\
                           "Automatic Tags":"identificators","Publisher":"publisher"},axis=1)
            for i in range(len(df)):
                df["keywords"].values[i] = df["keywords"].values[i].replace("*","")
                df["identificators"].values[i] = df["identificators"].values[i].replace("*","")
                if df["journal"].values[i].lower().startswith("http"):
                    df["journal"].values[i] = ""
                if re.search("\d+", df["AU"].values[i]) != None:
                    df["AU"].values[i] = ""
        if dataset_name in ["IDS", "Mastercard","ACET of Africa","CGSPACE","AFDB","IDRC","ABTAssociates","ACDIVOCA",\
                            "ACIAR","FANRPAN","Global Knowledge initiative","World VEG", "GIZ", "CDC", "WorldWatch", "FAO",\
                           "Horticulture","Postharvest Center","Rockfeller Foundation", "TechnoServe"]:
            df["url"]=""
            for i in range(len(df)):
                if dataset_name == "CGSPACE":
                    authors = []
                    split_parts = df["authors"].values[i].split(",")
                    for i in range(0,len(split_parts),2):
                        author_name = split_parts[i]
                        if i+1 < len(split_parts):
                            author_name + " , " + split_parts[i+1]
                        authors.append(author_name)
                    df["authors"].values[i] = ";".join(authors)
                if "abstract" in df.columns:
                    df["abstract"].values[i] = text_normalizer.clean_text_from_commas(df["abstract"].values[i])
                if "keywords" in df.columns:
                    df["keywords"].values[i] = df["keywords"].values[i].replace(",",";")
                df["url"].values[i] = df["file_urls"].values[i] if "file_urls" in df.columns and df["file_urls"].values[i] != "" else df["article_link"].values[i]
            df = df.rename({"authors":"AU","dataset_name":"dataset"},axis=1)
        if dataset_name in ["Wider"]:
            df["url"]=""
            df["raw_affiliation"] = ""
            for i in range(len(df)):
                df["raw_affiliation"].values[i] = "-".join(df["authors"].values[i].split("-")[1:])
                df["authors"].values[i] = df["authors"].values[i].split("-")[0].replace(",",";")
                df["keywords"].values[i] = df["keywords"].values[i].replace(",",";")
                df["abstract"].values[i] = text_normalizer.clean_text_from_commas(df["abstract"].values[i].strip())
                if type(df["year"].values[i]) == str:
                    year = parse(df["year"].values[i]).year
                    df["year"].values[i] = year
                df["url"].values[i] = df["file_urls"].values[i] if df["file_urls"].values[i] != "" else df["article_link"].values[i]
            df = df.rename({"authors":"AU","dataset_name":"dataset"},axis=1)
        df = df.rename({"authors":"AU","dataset_name":"dataset", "source_name":"dataset", "journal_name":"journal", "affiliation":"raw_affiliation"},axis=1)
        df = self.fill_required_fields(df, dataset_name)
        if dataset_name in ["WorldBank"]:
            df = text_normalizer.update_title_and_abstract_only_english(df)
        if dataset_name in ["Gardian"]:
            df = text_normalizer.update_title_and_abstract_only_english(df, ".", ".")
        df = self.fill_common_fields(df, dataset_name)
        if year_to_filter != None:
            df = df[df["year"]>=year_to_filter]
        return df[["AU","title","year","journal","abstract","url","raw_affiliation", "keywords", "email","identificators","dataset","publisher","dataset_type"]]

    def find_files(self, directory, pattern):
        for root, dirs, files in os.walk(directory):
            for basename in files:
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

    def load_big_dataset(self, directory = '..\model\student work'):
        big_dataset = pd.DataFrame()
        for filename in find_files(directory, '*.csv'):
            try:
                big_dataset = pd.concat([big_dataset, pd.read_csv(filename, encoding = "UTF-16", sep="\t", error_bad_lines=False).fillna("")], sort=False)
            except:
                print(filename)
        print("Dataset size: ", len(big_dataset))
        big_dataset = big_dataset.rename({"TI":"title",
                              "PY":"year",
                              "SO":"journal",
                              "AB":"abstract",
                              "GA":"raw_affiliation",
                              "DI":"url"
                             },axis=1)
        big_dataset["keywords"] = ""
        big_dataset["email"]=""
        big_dataset["identificators"] = ""
        big_dataset["dataset"] = "Science journals"
        for i in range(len(big_dataset)):
            big_dataset["url"].values[i] = self.create_link(big_dataset["url"].values[i])
            big_dataset['year'].values[i] = self.find_year(big_dataset['year'].values[i])
        return big_dataset[["AU","title","year","journal","abstract","url","raw_affiliation", "keywords", "email","identificators","dataset"]]