import pandas as pd
import requests
import json
import re
import sys
import numpy as np
import os
import nltk
import pickle
from sklearn.utils import shuffle

sys.path.append('../src')

from commons import elastic
from langdetect import detect
from text_processing import text_normalizer
from importlib import reload
from text_processing import duplicate_finder
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
import spacy
from dateutil.parser import parse
from utilities import excel_writer, excel_reader
from text_processing import abbreviations_resolver
from text_processing import search_engine_insensitive_to_spelling
from time import time
from interventions_labeling_lib import hyponym_search

stemmer = SnowballStemmer("english")
lmtzr = WordNetLemmatizer()
nlp = spacy.load('en_core_web_sm')

filter_word_list = text_normalizer.build_filter_dictionary(["../data/Filter_Geo_Names.xlsx"])

_abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver(filter_word_list)
_abbreviations_resolver.load_model("../model/abbreviations_dicts")

folder_to_save = "../tmp/cosai_hyponyms"
folder_with_excel = "../tmp/cosai-data"

for file in os.listdir(folder_with_excel):
    df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_excel, file))
    file_part = file.split(".")[0]
    t_start = time()
    search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(
        load_abbreviations = True)
    if os.path.exists("../model/cosai_index/%s" % file_part):
        search_engine_inverted_index.load_model("../model/cosai_index/%s" % file_part)
    else:
        search_engine_inverted_index.create_inverted_index(df)
        search_engine_inverted_index.save_model("../model/cosai_index/%s" % file_part)
    print("Time spent indexing: ", time() - t_start)
    
    file_to_save = os.path.join(folder_to_save, "hyponyms_found_%s.pickle"%file_part)
    os.makedirs(folder_to_save, exist_ok=True)
    if not os.path.exists(file_to_save):
        t_start = time()
        hyponyms_search = hyponym_search.HyponymsSearch()
        hyponyms_search.find_hyponyms_and_hypernyms(
                df, search_engine_inverted_index, file_to_save,
                columns_to_use=["title", "abstract"])
        pickle.dump(hyponyms_search, open(file_to_save,"wb"))
        print("Time spent hyponyms: ", time() - t_start)