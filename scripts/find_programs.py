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
from interventions_labeling_lib import programs_extractor
from interventions_labeling_lib import hyponym_search
from text_processing import search_engine_insensitive_to_spelling

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_or_folder_to_read')
    parser.add_argument('--abbreviations_dict', default = "../model/abbreviations_dicts")
    parser.add_argument('--columns_to_process', default="title,abstract")
    parser.add_argument('--folder_to_save_objects')
    parser.add_argument('--file_to_save')

    args = parser.parse_args()
    print("File or folder to read: %s" % args.file_or_folder_to_read)
    print("Abbreviations folder: %s" % args.abbreviations_dict)
    print("Abbreviations folder: %s" % args.columns_to_process)
    print("Folder to save objects: %s" % args.folder_to_save_objects)
    print("File to save: %s" % args.file_to_save)
    args.columns_to_process = [col.strip() for col in args.columns_to_process.split(",")]

    df = excel_reader.ExcelReader().read_df(args.file_or_folder_to_read)

    filter_word_list = text_normalizer.build_filter_dictionary(["../data/Filter_Geo_Names.xlsx"])

    _abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver()
    _abbreviations_resolver.load_model(args.abbreviations_dict)

    os.makedirs(args.folder_to_save_objects, exist_ok=True)

    search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(
        load_abbreviations = True, columns_to_process=args.columns_to_process)
    search_engine_inverted_index.create_inverted_index(df)

    _hyponyms_search = hyponym_search.HyponymsSearch()
    _hyponyms_search.find_hyponyms_and_hypernyms(df, search_engine_inverted_index,
        filename_with_data=os.path.join(args.folder_to_save_objects, "hyponyms_found_big_dataset_full.pickle"))

    _programs_extractor = programs_extractor.ProgramExtractor(filter_word_list)
    _programs_extractor.find_programs(_hyponyms_search, _abbreviations_resolver, file_with_found_programs=args.file_to_save,
            file_with_found_programs_filtered=args.file_to_save.replace(".xlsx", "_filtered.xlsx"))

    _hyponyms_search = hyponym_search.HyponymsSearch()
    global_hyponyms = pickle.load(open(os.path.join(args.folder_to_save_objects, "coref_hyponyms_gl.pickle"),"rb"))
    for article in global_hyponyms:
        _hyponyms_search.add_hyponyms(global_hyponyms[article],article)

    _programs_extractor = programs_extractor.ProgramExtractor(filter_word_list)
    _programs_extractor.find_programs(_hyponyms_search, _abbreviations_resolver, file_with_found_programs=args.file_to_save,
            file_with_found_programs_filtered=args.file_to_save.replace(".xlsx", "_filtered.xlsx"))
