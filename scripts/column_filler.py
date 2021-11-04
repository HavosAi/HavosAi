import sys
sys.path.append('../src')
import argparse
from utilities import excel_reader
from utilities import excel_writer
from text_processing import abbreviations_resolver
from text_processing import text_normalizer
from text_processing import search_engine_insensitive_to_spelling
from text_processing import all_column_filler
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_dataset', default ="", help='folder for dataset')
    parser.add_argument('--file_dataset', default = "", help='file for dataset')
    parser.add_argument('--folder_to_save', help='folder for saving')
    parser.add_argument('--abbreviations_dict', default = "../model/abbreviations_dicts", help="folder with abbreviations dict")
    parser.add_argument('--search_index_folder', default = "", help="folder with search index")
    parser.add_argument('--search_index_folder_pattern', default = "", help="folder pattern with search index")
    parser.add_argument('--settings', default = "column_setting.json", help="file with settings")

    args = parser.parse_args()

    if args.folder_dataset != "":
        print("Dataset folder: %s"%args.folder_dataset)
    else:
        print("Dataset file: %s"%args.file_dataset)
    print("Folder to save: %s"%args.folder_to_save)
    print("Folder with abbreviations %s"%args.abbreviations_dict)
    print("Folder with search index: %s"%args.search_index_folder)
    print("Folder pattern with search index: %s"%args.search_index_folder_pattern)
    print("File with column settings: %s"%args.settings)

    files_to_read = [args.file_dataset] if not args.folder_dataset else [
        os.path.join(args.folder_dataset, file) for file in os.listdir(args.folder_dataset)]

    _abbreviations_resolver = abbreviations_resolver.AbbreviationsResolver()
    _abbreviations_resolver.load_model(args.abbreviations_dict)

    os.makedirs(args.folder_to_save, exist_ok=True)

    for file in files_to_read:
        articles_df = excel_reader.ExcelReader().read_df_from_excel(file)
        base_filename = os.path.basename(file)
        if os.path.exists(os.path.join(args.folder_to_save, base_filename)):
            print("Already processed")
            continue

        search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(
            abbreviation_folder = args.abbreviations_dict, load_abbreviations = True)
        file_part = base_filename.split(".")[0]

        if not args.search_index_folder.strip():
            if not args.search_index_folder_pattern.strip():
                search_engine_inverted_index.create_inverted_index(articles_df)
            else:
                search_index_folder = args.search_index_folder_pattern % file_part
                print("Load index from ", search_index_folder)
                search_engine_inverted_index.load_model(search_index_folder)
                print("Search index is loaded...")
        else:
            search_engine_inverted_index.load_model(args.search_index_folder)
            print("Search index is loaded...")

        _all_column_filler = all_column_filler.AllColumnFiller()
        articles_df = _all_column_filler.fill_columns_for_df(articles_df, search_engine_inverted_index, _abbreviations_resolver, args.settings)

        excel_writer.ExcelWriter().save_df_in_excel(articles_df, os.path.join(args.folder_to_save, base_filename))