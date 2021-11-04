import sys
sys.path.append('../src')

from text_processing import topic_modeling
from text_processing import text_normalizer
from text_processing import search_engine_insensitive_to_spelling
from utilities import excel_writer
from utilities import excel_reader

import argparse
import pandas as pd
import pickle
import os

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--folder_dataset',help='folder for dataset')
	parser.add_argument('--filename_dataset', help='file for dataset')
	parser.add_argument('--n_topics', default = 150, help='quantity of topics')
	parser.add_argument('--folder', default = "../model/nmf_model_new_3_grams_big_dataset",help='folder for saving')
	parser.add_argument('--file_search', default = "../model/search_index_3", help="folder with search inverted index")
	parser.add_argument('--use_3_grams', dest='use_3_grams', action='store_true')
	parser.add_argument('--use_bigrams', dest='use_3_grams', action='store_false')
	parser.set_defaults(use_3_grams=True)
	parser.add_argument('--label_columns', dest='label_columns', action='store_true', help="label columns with new topics in articles_df")
	parser.set_defaults(label_columns=False)

	args = parser.parse_args()
	args.n_topics = int(args.n_topics)

	if args.folder_dataset:
		print("dataset folder: %s"%args.folder_dataset)
	else:
		print("dataset file: %s"%args.filename_dataset)
	print("Folder to save: %s"%args.folder)
	print("Number of topics %d"%args.n_topics)
	print("folder with search %s"%args.file_search)
	print("Used 3 grams" if args.use_3_grams else "Used bigrams")
	print("Label columns" if args.label_columns else "No label columns")

	if args.folder_dataset:
		articles_df = excel_reader.ExcelReader().read_distributed_df_from_excel(args.folder_dataset)
	else:
		articles_df = excel_reader.ExcelReader().read_df_from_excel(args.filename_dataset)
	print("Dataset is loaded ...")

	filter_word_list = text_normalizer.build_filter_dictionary(["../data/Filter_Geo_Names.xlsx", "../data/map_plant_products.xlsx", "../data/map_animal_products.xlsx"])
	topic_modeler = topic_modeling.TopicModeler(filter_word_list, args.n_topics, max_df= 0.1, min_df = 0.0001, use_3_grams=args.use_3_grams)

	topic_modeler.model_topics(articles_df, 20)
	topic_modeler.save_model(args.folder)

	search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(filter_word_list, load_abbreviations = True)
	search_engine_inverted_index.load_model(args.file_search)
	topic_modeler.calculate_statistics_by_topics(search_engine_inverted_index, articles_df)
	topic_modeler.export_statistics(articles_df, os.path.join(args.folder, "%d topics %s.xlsx"%(args.n_topics, os.path.basename(args.folder))))

	if args.label_columns:
		articles_df = topic_modeler.fill_topic_for_articles(articles_df, search_engine_inverted_index, column_name="topics_1", topic_mode="raw topic")
		articles_df = topic_modeler.fill_topic_for_articles(articles_df, search_engine_inverted_index, column_name="topics_keywords_1", topic_mode="topic keywords")
		articles_df = topic_modeler.fill_topic_for_articles(articles_df, search_engine_inverted_index, column_name="topics_hierarchy_1", topic_mode="topic hierarchy")

		excel_writer.ExcelWriter().save_big_data_df_in_excel(articles_df,os.path.join(args.folder, "dataset_with_topics"))