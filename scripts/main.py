import pandas as pd
import requests
import json
import re
import sys
import numpy as np
import os
import nltk

sys.path.append('../src')
from commons import elastic

from utilities import excel_reader
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_with_dataset', default="big_dataset_distributed", help='folder for dataset')
    parser.add_argument('--elastic_index_name', default="articles", help='elastic index name for dataset')
    parser.add_argument('--elastic_host')
    parser.add_argument('--kibana_host')
    
    args = parser.parse_args()
    print("Folder with dataset: %s"%args.folder_with_dataset)
    print("Index name: %s"%args.elastic_index_name)
    print("Elastic host: %s"%args.elastic_host)
    print("Kibana host: %s"%args.kibana_host)

    es = elastic.ElasticClient(args.elastic_host,
                          args.kibana_host, "", "")

    es.bulk_index_big_data(
        args.folder_with_dataset,
        properties={
            'title':      {'type': 'text'},
            'abstract':   {'type': 'text'},
            'url':        {'type': 'keyword'},
            'author':     {'type': 'keyword'},
            'dataset':    {'type': 'keyword'},
            'year':       {'type': 'date'},
            'affiliation': {'type': 'keyword'},
            'topics': {'type':'keyword'},
            'countries_mentioned': {'type':'keyword'},
            'country_codes': {'type':'keyword'},
            'animal_products_search': {'type':'keyword'},
            'plant_products_search': {'type':'keyword'},
            'interventions_found': {'type': 'keyword'},
            'normalized_key_words':{'type':'keyword'},
            'journal':{'type':'keyword'},
            'geo_regions':{'type':'keyword'},
            'world_bankdivision_regions':{'type':'keyword'},
            'outcomes_found':{'type':'keyword'},
            'intervention_labels':{'type':'keyword'},
            'technology intervention':{'type':'keyword'},
            'socioeconomic intervention':{'type':'keyword'},
            'ecosystem intervention':{'type':'keyword'},
            'storage intervention':{'type':'keyword'},
            'topics_hierarchy':{'type':'keyword'},
            'topics_keywords':{'type':'keyword'},
            'measurements':{'type':'keyword'},
            "programs_found":{"type":"keyword"},
            "mechanisation intervention":{"type":"keyword"},
            "measurements_for_interventions":{"type":"keyword"},
            "measurements_for_crops":{"type":"keyword"},
            "population tags":{"type":"keyword"},
            "dataset_type":{"type":"keyword"},
            "team_tags":{"type":"keyword"},
            "study_type":{"type":"keyword"},
            "provinces":{"type":"keyword"},
            "districts":{"type":"keyword"},
            "is_used_in_full_text_search":{"type":"keyword"},
            "compared_terms":{"type":"keyword"}
        },
        index_name=args.elastic_index_name,
        time_field='year',
        create_search=False
    )