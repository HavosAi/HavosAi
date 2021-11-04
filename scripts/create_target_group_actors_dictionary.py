import sys
sys.path.append('../src')

from text_processing import text_normalizer
from utilities import excel_writer, excel_reader
import argparse
import pickle
import os
from time import time
import nltk
import re
from text_processing import concepts_merger
from text_processing import search_engine_insensitive_to_spelling
import pandas as pd
from synonyms_module import synonyms_processor
import numpy as np
import hdbscan

def get_word_expression_embedding(_syn, sentence):
    word_expressions = set()
    for sent in sentence.split(";"):
        for phr in _syn.phrases[text_normalizer.get_stemmed_words_inverted_index(text_normalizer.normalize_text(sent.strip()))]:
            word_expressions.add(phr.replace("_", " "))
    vec = np.zeros(300)
    for word in word_expressions:
        #if word in _syn.google_model.wv:
        #    vec += _syn.google_model.wv[word]
        if word in _syn.fast_text_model.wv:
            vec += _syn.fast_text_model.wv[word]
        else:
            print("%s is not found (%s)"%(word, sentence))
    return vec if len(word_expressions) == 0 else vec/(len(word_expressions))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_to_read',
        default = "C:/Users/Maryia_Ivanina/Downloads/FINAL_VC Stocktaking Database 2010-2018_with_our_columns.xlsx")
    parser.add_argument('--columns_to_take', default = "VC\nEntry Point ;Target Group/Beneficiaries;Type of PS Actors Involved")
    parser.add_argument('--file_to_save', default = "")
    parser.add_argument('--word_embeddings_folder', default = "../model/synonyms_retrained_new")


    args = parser.parse_args()

    print("File to read: %s"%args.file_to_read)
    print("Columns to take: %s"%args.columns_to_take)
    print("File to write: %s"%args.file_to_save)
    print("Folder with embeddings: %s"%args.word_embeddings_folder)

    args.columns_to_take = list(filter(lambda x: x.strip(), args.columns_to_take.split(";")))

    df = excel_reader.ExcelReader().read_df_from_excel(args.file_to_read)
    split_phrases = {}
    for i in range(len(df)):
        for column in args.columns_to_take:
            prepared_line = re.sub(
                r"\b(and|or|;|in particular|including|focus on|whose)\b", ",",
                df[column].values[i].replace("\n",",").replace("\\", ",").replace("/",","), flags=re.IGNORECASE)
            prepared_line = re.sub(r"\(\s*[\w\d]{1,4}\s*\)", "", prepared_line)
            prepared_line = prepared_line.replace("(", ",").replace(")", ",")
            prepared_line = re.sub(r"\bHH\b", "household", prepared_line)
            split_w = [text_normalizer.normalize_sentence(w) for w in prepared_line.split(",")]
            for w in split_w:
                if not w.strip():
                    continue
                if w not in split_phrases:
                    split_phrases[w] = 0
                split_phrases[w] += 1

    search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling(load_abbreviations = False)
    search_engine_inverted_index.create_inverted_index(pd.DataFrame({"title": [""]*len(split_phrases), "abstract": list(split_phrases.keys())}))

    _concepts_merger = concepts_merger.ConceptsMerger(3)
    for idx, w in enumerate(split_phrases.keys()):
        _concepts_merger.add_item_to_dict(w, 0)
    _concepts_merger.merge_concepts(search_engine_inverted_index, threshold=0.88)

    for key in _concepts_merger.new_mapping:
        if key != _concepts_merger.new_mapping[key]:
            print(key, " $$$ ", _concepts_merger.new_mapping[key])

    
    _syn = synonyms_processor.SynonymsProcessor(folder=args.word_embeddings_folder)

    words = []
    word_embeddings = []
    words_set = set()
    for w in split_phrases:
        if len(w.split()) <= 4:
            if w in _concepts_merger.new_mapping:
                w = _concepts_merger.new_mapping[w]
            if w not in words_set:
                words.append(w)
                word_embeddings.append(get_word_expression_embedding(_syn, w))
                words_set.add(w)

    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1)
    cluster_labels = clusterer.fit_predict(word_embeddings)

    cluster_vals = {}
    for i in range(len(words)):
        if cluster_labels[i] != -1:
            if cluster_labels[i] not in cluster_vals:
                cluster_vals[cluster_labels[i]] = []
            cluster_vals[cluster_labels[i]].append(words[i])

    cluster_names = {}
    for val in cluster_vals:
        maxword_cnt = np.argmax([split_phrases[w] for w in cluster_vals[val]])
        
        print(val, cluster_vals[val][maxword_cnt])
        cluster_names[val] = cluster_vals[val][maxword_cnt]
        for w in cluster_vals[val]:
            print("--- ", w)

    prepared_dictionary = []
    for i in range(len(words)):
        if cluster_labels[i] >= 0:
            all_found_words = [words[i]] if words[i] not in _concepts_merger.inverted_dictionary else _concepts_merger.inverted_dictionary[words[i]]
            for w in all_found_words:
                prepared_dictionary.append((w, cluster_names[cluster_labels[i]]))
        else:
            all_found_words = [words[i]] if words[i] not in _concepts_merger.inverted_dictionary else _concepts_merger.inverted_dictionary[words[i]]
            for w in all_found_words:
                prepared_dictionary.append((w, words[i]))

    excel_writer.ExcelWriter().save_data_in_excel(prepared_dictionary, ["Keyword", "High level label"], args.file_to_save)
