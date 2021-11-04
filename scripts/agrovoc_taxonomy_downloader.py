import sys
sys.path.append('../src')

from commons import download_agrovoc_taxonomy
from utilities import excel_writer
import argparse
import pandas as pd
import pickle
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_dataset_to_save', default = "../tmp/")
    parser.add_argument('--keywords', default = "")
    parser.add_argument('--languages', default = "en")


    args = parser.parse_args()

    print("Folder to save: %s"%args.folder_dataset_to_save)
    print("Keywords: %s"%args.keywords)
    print("Languages: %s"%args.languages)

    keywords = args.keywords.split(",")

    _downloader = download_agrovoc_taxonomy.AgrovocTaxonomyDownloader()
    _downloader.get_mappings_for_2_level_terms(
    	keywords, chosen_languages=args.languages, file_folder=args.folder_dataset_to_save)