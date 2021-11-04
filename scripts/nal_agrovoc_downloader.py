import sys
sys.path.append('../src')

from commons import nal_taxonomy_download
from utilities import excel_writer
import argparse
import pandas as pd
import pickle
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_to_save', default = "")
    parser.add_argument('--urls', default = "")


    args = parser.parse_args()

    print("File to save: %s"%args.file_to_save)
    print("Urls: %s"%args.urls)

    _downloader = nal_taxonomy_download.NalTaxonomyDownloader()
    _downloader.create_ontology(
    	[_downloader.gather_ontology(url) for url in args.urls.split(",")], args.file_to_save)