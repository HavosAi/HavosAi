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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_or_folder_to_read', default = "")
    parser.add_argument('--use_prefix', default= "")
    parser.add_argument('--columns_to_use', default= "abstract,title")
    parser.add_argument('--folder_to_save', default = "../model/abbreviations_dicts")

    args = parser.parse_args()
    print("File or folder to read: %s" % args.file_or_folder_to_read)
    print("Use prefix: %s" % args.use_prefix)
    print("Columns to use: %s" % args.columns_to_use)
    print("Folder to save: %s" % args.folder_to_save)
    args.columns_to_use = [col.strip() for col in args.columns_to_use.split(",")]

    df = excel_reader.ExcelReader().read_df(args.file_or_folder_to_read)

    filter_word_list = text_normalizer.build_filter_dictionary(["../data/Filter_Geo_Names.xlsx"])

    _abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver(filter_word_list)
    _abbreviations_resolver.load_model(args.folder_to_save)
    _abbreviations_resolver.extract_hyponym_abbreviations(
        df, continue_extract=True, use_prefix=args.use_prefix, columns_to_use=args.columns_to_use)
    _abbreviations_resolver.save_model(args.folder_to_save)
    _abbreviations_resolver.resolve_abbreviations()
    _abbreviations_resolver.save_model(args.folder_to_save)