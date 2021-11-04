import sys
sys.path.append('../src')

from text_processing import text_normalizer
from utilities import excel_writer, excel_reader
import argparse
import pandas as pd
import pickle
import os
from time import time
import nltk
import re
from text_processing import abbreviations_resolver
from text_processing import all_column_filler
from text_processing import search_engine_insensitive_to_spelling

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_to_read', default = "")

    args = parser.parse_args()

    print("File to read: %s"%args.file_to_read)


    _abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver([])
    _abbreviations_resolver.load_model("../model/abbreviations_dicts")


    df = excel_reader.ExcelReader().read_df_from_excel(args.file_to_read)
    print(len(df))
    df = df.rename({"title":"old_title"}, axis=1)
    df["title"] = ""
    df["abstract"] = df["several_sentences"]
    search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(load_abbreviations = True)
    search_engine_inverted_index.create_inverted_index(df)
    _all_column_filler = all_column_filler.AllColumnFiller()
    df = _all_column_filler.fill_columns_for_df(df, search_engine_inverted_index, _abbreviations_resolver,settings_json = {"columns":[
        #{"column_filler_class":"KeywordNormalizer"},
        #{"column_filler_class":"JournalNormalizer"},
        #{"column_filler_class":"AuthorAndAuthorAffiliationExtractor"},
        #{"column_filler_class":"GeoNameFinder", "use_cache": True, "columns_with_country_code": ["country_code"]},
        #{"column_filler_class":"CropsSearch", "file_dictionary":"../notebooks/plant_products_with_foreign.xlsx", "column_name":"plant_products_search"},
        #{"column_filler_class":"CropsSearch", "file_dictionary":"../notebooks/animal_products_with_foreign.xlsx", "column_name":"animal_products_search"},
        #{"column_filler_class":"CropsSearch", "column_name": "animals_found", "keep_hierarchy": False, 
        #"file_dictionary":"../notebooks/animals_with_foreign.xlsx"},
        #{"column_filler_class":"ColumnFiller", "column_name": "target_group_actors", "column_details": "target_group_actors_details",
    #"keep_hierarchy": True, "column_dictionary":"../notebooks/target_group_actors_with_foreign.xlsx"},
        #{"column_filler_class":"CropsSearch", "file_dictionary":"../data/map_plant_products_wo_foreign.xlsx", "threshold":0.9, "column_name":"plant_products_search"},
        #{"column_filler_class":"CropsSearch", "file_dictionary":"../data/map_animal_products_wo_foreign.xlsx", "threshold":0.9, "column_name":"animal_products_search"},
        #{"column_filler_class":"PopulationTagsFinder"},
        #{"column_filler_class":"ColumnFiller", "column_name": "cross_cutting_issues", "column_details": "cross_cutting_issues_details", "column_dictionary":"../data/cross_cutting_themes.xlsx"},
        #{"column_filler_class":"ColumnFiller", "column_name": "outcomes_found", "column_details": "outcomes_details", "column_dictionary":"../tmp/outcomes_with_foreign.xlsx"},
        #{"column_filler_class":"ColumnDataRenamer", "values_dict":{ "Gender": "Gender empowerment"}, "column_to_rename": "outcomes_found"},
        #{"column_filler_class":"TopicModeler", "model_folder":"../model/nmf_3grams_all_reweight_125", "folder_for_wordvec":"../model/synonyms_retrained_new"},
        #{"column_filler_class":"ProgramExtractor"},
        #{"column_filler_class":"ComparedTermsLabeller"},
        #{"column_filler_class":"CropsSearch", "column_name": "animals_found", 
        #"keep_hierarchy": False, "file_dictionary":"../data/map_animals.xlsx"},
        #{"column_filler_class":"ColumnFiller", "column_name": "gender_age_population_tags", 
        #"keep_hierarchy": False, "column_dictionary":"../data/population_tags.xlsx"},
        #{"column_filler_class":"InterventionsSearchForLabeling", "file":"../tmp/interventions.xlsx"}
        #{"column_filler_class":"MeasurementsLabeler", "folder_with_measurements":"../tmp/dfs_measurements"}
        {"column_filler_class": "GRIPSClassifier", "word_embeddings_folder": "../model/ifad_word_embeddings",
        "subcategory_column": "new_subcategory", "category_column": "new_category"},
        #{"column_filler_class": "InterventionLabeller", "interventions_model_folder": "../model/intervention_labels_model",
        #"word2vec_model_folder": "../model/synonyms_retrained_new", "narrow_concept_column": "context"}
    ]})
    df["title"] = df["old_title"]
    df = df.drop(["old_title"], axis=1)
    excel_writer.ExcelWriter().save_df_in_excel(df, args.file_to_read)