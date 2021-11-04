import sys
sys.path.append('../src')

from text_processing import text_normalizer
from utilities import excel_writer, excel_reader
import argparse
import pandas as pd
import pickle
import os
from interventions_labeling_lib import hyponym_statistics
from time import time
import nltk
import re

_hyp_stat = hyponym_statistics.HyponymStatistics({}, {}, {}, {}, {})

def clean_from_filter_words(sentence, filter_words):
    words = text_normalizer.normalize_sentence(sentence).split()
    filtered_words = []
    i = 0
    while i < len(words):
        add_word = True
        for j in [3,2,1]:
            if " ".join(words[i: i+j]) in filter_words:
                i += j
                add_word = False
                break
        if add_word:
            filtered_words.append(words[i])
            i += 1
    if len(filtered_words):
        return text_normalizer.normalize_sentence(sentence)
    return ""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_to_read', default = "")
    parser.add_argument('--folder_to_write', default = "../tmp/results_ifad_contexts_new")


    args = parser.parse_args()

    print("File to read: %s"%args.file_to_read)
    print("Folder to write: %s"%args.folder_to_write)

    os.makedirs(args.folder_to_write, exist_ok=True)

    stopwords_crops = set(excel_reader.ExcelReader().read_df_from_excel("../data/Filter_Geo_Names.xlsx")["Word"].values)
    for file in ["map_animals.xlsx", "map_plant_products_wo_foreign.xlsx", "map_animal_products_wo_foreign.xlsx"]:
        df_1 = excel_reader.ExcelReader().read_df_from_excel(os.path.join("../data", file))
        stopwords_crops = stopwords_crops.union(set(df_1["narrow_name"].values))
        stopwords_crops = stopwords_crops.union(set(df_1["broad_name"].values))
        stopwords_crops = stopwords_crops.union(set(df_1["level_3_term"].values))

    stopwords_crops_normalized = set()
    for word in stopwords_crops:
        stopwords_crops_normalized.add(text_normalizer.normalize_sentence(word))
    stopwords_crops_normalized = stopwords_crops_normalized.union(set(["aquaculture product", "including"]))

    all_crops = set()
    for file in ["map_animals.xlsx", "map_plant_products_wo_foreign.xlsx", "map_animal_products_wo_foreign.xlsx"]:
        df_1 = excel_reader.ExcelReader().read_df_from_excel(os.path.join("../data", file))
        all_crops = all_crops.union(set(df_1["narrow_name"].values))
        all_crops = all_crops.union(set(df_1["broad_name"].values))
        all_crops = all_crops.union(set(df_1["level_3_term"].values))
    all_crops = set([text_normalizer.normalize_sentence(crop) for crop in all_crops]) - set([""])

    df = excel_reader.ExcelReader().read_df_from_excel(args.file_to_read)
    all_contexts = []
    cnt = 0
    for i in range(len(df)):
        if i % 10000 == 0:
            print("%d processed" % i)
        #if df["intervention"].values[i] != "fish marketing":#i != 28:
        #    continue
        #print(i)
        #print(df["intervention"].values[i])
        #print(df["context"].values[i])
        #print(df["real_sentence"].values[i])
        normalized_sent = text_normalizer.normalize_sentence(df["context"].values[i]).split()
        words_and_punkt = nltk.wordpunct_tokenize(df["real_sentence"].values[i])
        first_ind = []
        last_ind = []
        for idx in range(len(words_and_punkt)):
            if text_normalizer.normalize_sentence(words_and_punkt[idx]) == normalized_sent[0]:
                first_ind.append(idx)
            if text_normalizer.normalize_sentence(words_and_punkt[idx]) == normalized_sent[-1]:
                last_ind.append(idx)
        part_sentence = ""
        for ind_1 in first_ind:
            for ind_2 in last_ind:
                if text_normalizer.normalize_sentence(" ".join(words_and_punkt[ind_1: ind_2+1])) == df["context"].values[i]:
                    part_sentence = " ".join(words_and_punkt[ind_1: ind_2+1])
        #print(part_sentence)
        time_1 = time()
        #print(part_sentence)
        #print(df["intervention_type"].values[i])
        check_values = [df["intervention"].values[i]]
        if df["intervention_type"].values[i] in ["plant products driven", "animal products driven", "animals driven"]:
            check_values = all_crops
        right_contexts = []
        found_crops = set()
        empty_contexts = []
        for context_split in text_normalizer.split_sentence_to_parts(part_sentence, remove_and_or=True):
            nothing_found = True
            for val in check_values:
                if val in text_normalizer.normalize_sentence(context_split):
                    nothing_found = False
                    if re.search(r"\b%s"%val, text_normalizer.normalize_sentence(context_split)):
                        if df["intervention_type"].values[i] != "standard" and "product" not in val and re.search(
                            r"\b%s\b"%val, text_normalizer.normalize_sentence(context_split)):
                            found_crops.add(val)
                        right_contexts.append((val, text_normalizer.normalize_sentence(context_split).strip()))
            if nothing_found:
                empty_contexts.append(text_normalizer.normalize_sentence(context_split).strip())
            if df["intervention_type"].values[i] == "standard":
                for val in all_crops:
                    if val in text_normalizer.normalize_sentence(context_split) and "product" not in val:
                        if re.search(r"\b%s\b"%val, text_normalizer.normalize_sentence(context_split)):
                            found_crops.add(val)
        new_contexts = []
        for name, context in right_contexts:
            new_contexts.append(context)
            for crop in sorted(found_crops, key=lambda x: (len(x.split()), len(x)), reverse=True):
                context = re.sub(r"\b%s\b"%crop, " ## ", context)
            context = re.sub("(\s*##\s*)+", " ## ", context)
            for crop in found_crops:
                new_context = re.sub("##", crop, context)
                new_contexts.append(new_context)
        
        if df["intervention_type"].values[i] != "standard":
            for empty_context in empty_contexts:
                for crop in sorted(found_crops, key=lambda x: (len(x.split()), len(x)), reverse=True):
                    empty_context = re.sub(r"\b%s\b"%crop, " ## ", empty_context)
                empty_context = re.sub("(\s*##\s*)+", " ## ", empty_context)
                if "#" not in empty_context:
                    empty_context = "## " + empty_context
                for crop in found_crops:
                    new_context = re.sub("##", crop, empty_context)
                    new_contexts.append(new_context)
        
        full_new_contexts = []
        for context in new_contexts:
            new_context = context
            if " ".join(new_context.split()[-2:]) == "nb batch":
                new_context = " ".join(new_context.split()[:-2])
            if new_context.split()[-1] == "nb":
                new_context = " ".join(new_context.split()[:-1])
            full_new_contexts.append(new_context)
                
        new_contexts = set([clean_from_filter_words(context, stopwords_crops_normalized) for context in full_new_contexts]) - set([""])
        full_context_rows = []
        if df["intervention_type"].values[i] == "standard":
            for context in new_contexts:
                if df["intervention"].values[i] in context:
                    full_context_rows.append((df["intervention"].values[i], context))
                else:
                    full_context_rows.append((context, context))
        else:
            for context in new_contexts:
                full_context_rows.append((context, context))

        if not full_context_rows:
            print(i)
            print(df["intervention_type"].values[i])
            print(df["intervention"].values[i])
            print(df["context"].values[i])
            print(df["real_sentence"].values[i])
        all_contexts.append(full_context_rows)
    file_save = os.path.basename(args.file_to_read) + ".pickle"
    pickle.dump(all_contexts, open(os.path.join(args.folder_to_write,file_save), "wb"))

    