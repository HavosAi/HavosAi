import sys
sys.path.append('../src')

from text_processing import text_normalizer
from text_processing import search_engine_insensitive_to_spelling
from utilities import excel_writer
from utilities import excel_reader
from interventions_labeling_lib import hyponym_search
from interventions_labeling_lib import hearst_pattern_finder
from interventions_labeling_lib import hyponym_statistics
from interventions_labeling_lib import coreferenced_concepts_finder
from interventions_labeling_lib import storage_interventions_finder
from interventions_labeling_lib import sentence_with_intervention_labeler
from interventions_labeling_lib import programs_extractor
from text_processing import abbreviations_resolver

import argparse
import pandas as pd
import pickle
import os

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--folder_dataset', default = "new_big_dataset", help='folder for dataset')
	parser.add_argument('--filename', default = "../model/sentence_parsing_big_dataset.pickle",help='filename for saving')
	parser.add_argument('--file_search', default = "../model/search_index_3", help="folder with search inverted index")

	args = parser.parse_args()

	print("dataset folder: %s"%args.folder_dataset)
	print("File to save: %s"%args.filename)
	print("folder with search %s"%args.file_search)

	filter_word_list = text_normalizer.build_filter_geo_points_dictionary("../data/Filter_Geo_Names.xlsx")

	search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(filter_word_list, load_abbreviations = True)
	search_engine_inverted_index.load_model(args.file_search)

	_abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver(filter_word_list)
	_abbreviations_resolver.load_model("../model/abbreviations_dicts")
	_abbreviations_resolver.resolve_abbreviations()

	articles_df = excel_reader.ExcelReader().read_distributed_df_from_excel(args.folder_dataset)
	articles_df_1 = articles_df[["title","title_translated","abstract_translated","abstract"]]
	articles_df = articles_df_1
	articles_df_1 = []
	print("Dataset is loaded ...")

	key_word_mappings = ["practice", "approach", "intervention", "input","strategy", "policy", "program", "programme",\
	 "initiative", "technology", "science", "technique", "innovation", "biotechnology","machine", "mechanism", "equipment","tractor","device","machinery","project"]

	_sentence_with_intervention_labeler = sentence_with_intervention_labeler.SentenceWithInterventionsLabeler(filter_word_list)
	_sentence_with_intervention_labeler.parse_sentences(articles_df, search_engine_inverted_index, key_word_mappings,parse=True,filename=args.filename)

	_programs_extractor = programs_extractor.ProgramExtractor(filter_word_list)
	_programs_extractor.find_programs(_sentence_with_intervention_labeler.hyponyms_search_part, _abbreviations_resolver)