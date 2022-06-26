import gensim
import os
import re
import nltk
import sys
import unicodedata
import traceback
import pickle
import numpy as np
import pandas as pd
from gensim.models.phrases import Phrases, Phraser

def get_script_directory():
    path = os.path.realpath(sys.argv[0])
    if os.path.isdir(path):
        return path
    else:
        return os.path.dirname(path)

sys.path.append(os.path.join(get_script_directory(),"src"))

from text_processing import text_normalizer
from text_processing import search_engine_insensitive_to_spelling
from utilities import excel_writer

class SynonymsSearch:

    def __init__(self, model_folder):
        self.phrases = Phraser.load(os.path.join(model_folder, "phrases_bigram.model"))
        self.phrases_3gram = Phraser.load(os.path.join(model_folder, "phrases_3gram.model"))
        self.fast_text_model = gensim.models.FastText.load(os.path.join(model_folder, "fast_text_our_dataset/fast_text_our_dataset.model"))
        self.google_model_2_and_3_grams = gensim.models.Word2Vec.load(os.path.join(model_folder, "google_2_and_3_bigrams_our_dataset/google_2_and_3_bigrams_our_dataset.model"))
        self.search_engine_inverted_index = search_engine_insensitive_to_spelling.SearchEngineInsensitiveToSpelling()
        self.search_engine_inverted_index.load_model(os.path.join("../model/","search_index_study_design_df/"))

        with open(os.path.join(model_folder,"invert_index_and_popular_expressions.pckl"), 'rb') as f:
            self.inverted_index_n_grams, self.popular_expressions = pickle.load(f)

#         with open(os.path.join(model_folder,"resolved_abbreviations.pickle"), 'rb') as f:
#             self.sorted_resolved_abbreviations, self.sorted_words_to_abbreviations = pickle.load(f)

    def get_frequency_as_expression(self, query):
        if query in self.inverted_index_n_grams:
            return self.inverted_index_n_grams[query]
        return 0

    def prepare_df(self, df, reodered_columns, new_mapping, columns_to_delete=[]):
        if len(df) != 0:
            reodered_columns_for_df = []
            for column in reodered_columns:
                if column in df.columns:
                    reodered_columns_for_df.append(column)
            df = df[reodered_columns_for_df]
            for column in columns_to_delete:
                if column in df.columns:
                    df = df.drop(columns=[column])
        df = df.rename(new_mapping, axis=1)
        df = df.rename({"word":"Word"}, axis=1)
        return df

    def prepare_dfs_for_excel(self, query, word_count, new_mapping, all_tab_names):
        synonym_words = self.get_synonyms(query, word_count)
        if len(synonym_words) == 0:
            synonym_words, not_known_words = self.get_approximate_synonyms(query, word_count)
        reodered_columns = ["word","similarity","coocurence","frequency_as_expression", "frequency","percent_frequency"]
        synonym_words = self.prepare_df(pd.DataFrame(synonym_words), reodered_columns, new_mapping)
        suggested_words = self.prepare_df(pd.DataFrame(self.get_suggested_words(query)), reodered_columns, new_mapping,["similarity"])
        popular_expressions = self.prepare_df(pd.DataFrame(self.get_popular_expressions(query)), reodered_columns, new_mapping,["similarity"])
        abbr_array = self.get_abbreviations_for_word(query)
        abbr_array.extend(self.get_word_expressions_for_abbreviation(query))
        abbreviations = self.prepare_df(pd.DataFrame(abbr_array), reodered_columns, new_mapping,["similarity"])
        res_dfs = []
        tab_names = []
        for idx, df in enumerate([synonym_words, suggested_words, popular_expressions, abbreviations]):
            if len(df) > 0:
                res_dfs.append(df)
                tab_names.append(all_tab_names[idx])
        return res_dfs, tab_names

    def generate_excel(self, query, word_count):
        new_mapping = {"similarity":"Similarity Measure", "frequency":"Document frequency in the corpus",\
         "frequency_as_expression":"Document frequency as an indivisible expression in the corpus","percent_frequency":"Document frequency in the corpus(%)",
         "coocurence":"Word expression frequency identified by the abbreviation"}
        all_tab_names = ["Synonyms", "Suggested words by spelling", "Popular word expressions","Abbreviations"]
        dfs, tab_names = self.prepare_dfs_for_excel(query, word_count, new_mapping, all_tab_names)
        try:
            return excel_writer.ExcelWriter().encode_excel_base64(dfs,\
            tab_names, column_probabilities=new_mapping.values())
        except:
            traceback.print_exc()
        return ""

    def get_frequency_for_word(self, word):
        res = self.search_engine_inverted_index.find_articles_with_keywords([word],1.0,extend_query = False, extend_with_abbreviations = False)
        return res[0][1] if len(res) > 0 else 0

    def get_frequency_in_percent(self, word):
        return round(self.get_frequency_for_word(word)*100/self.search_engine_inverted_index.total_articles_number,3)

    def get_approximate_synonyms(self, query, word_count):
        normalize_query = text_normalizer.normalize_sentence(query)
        sorted_words = []
        words_in_query_count = len(normalize_query.split())
        if words_in_query_count == 0:
            return [], []
        not_known_words = set()
        for word in normalize_query.split():
            if word not in self.google_model_2_and_3_grams.wv:
                not_known_words.add(word)
        try:
            sorted_words = self.calculate_details_about_synonyms(normalize_query, self.fast_text_model.wv.most_similar(normalize_query, topn=word_count))
        except:
            return [], list(not_known_words)
        return sorted_words, list(not_known_words)

    def calculate_details_about_synonyms(self, normalize_query, sorted_words):
        words = [{"word":normalize_query, "similarity":1.0, "frequency":self.get_frequency_for_word(normalize_query),\
             "percent_frequency":self.get_frequency_in_percent(normalize_query), "frequency_as_expression":self.get_frequency_as_expression(normalize_query)}]
        for word in sorted_words:
            words.append({"word":word[0], "similarity":round(word[1],3), "frequency":self.get_frequency_for_word(word[0]), "percent_frequency":self.get_frequency_in_percent(word[0]),
                 "frequency_as_expression":self.get_frequency_as_expression(word[0])})
        return words

    def get_word_expression_embedding(self, model, sentence, use_3_gram=False):
        word_expressions = set()
        phrases = self.phrases[text_normalizer.get_stemmed_words_inverted_index(sentence.strip())]
        if use_3_gram:
            phrases = self.phrases_3gram[phrases]
        for phr in phrases:
            word_expressions.add(phr.replace("_", " "))
        vec = np.zeros(300)
        for word in word_expressions:
            if word in model.wv:
                vec += model.wv[word]
            else:
                normalized_word = " ".join(text_normalizer.get_stemmed_words_inverted_index(word.lower()))
                if normalized_word in model.wv:
                    vec += model.wv[normalized_word]
        return vec if len(word_expressions) == 0 else vec/(len(word_expressions))


    def find_synonyms_by_several_models(self, models, query, n_words):
        words = []
        words_with_scores = {}
        total_not_found = 0
        normalize_query = text_normalizer.normalize_sentence(query)
        for model in models:
            try:
                avg_vector = self.get_word_expression_embedding(model, normalize_query, use_3_gram=True)
                for word in model.wv.similar_by_vector(avg_vector, topn=n_words+1):
                    normalized_word = word[0]
                    if normalized_word == normalize_query:
                        continue
                    if word[1] < 0.05:
                        continue
                    if normalized_word not in words_with_scores:
                        words_with_scores[normalized_word] = 0.0
                    words_with_scores[normalized_word] = max(words_with_scores[normalized_word], word[1])
            except Exception:
                total_not_found += 1
        if total_not_found == len(models):
            print("Word %s is not found in the vocabulary" %query)
        else:
            sorted_words = sorted(words_with_scores.items(),key=lambda x:x[1], reverse=True)
            words = self.calculate_details_about_synonyms(normalize_query, sorted_words[:n_words])
        return words

    def get_synonyms(self, word, word_count = 20):
        return self.find_synonyms_by_several_models([self.google_model_2_and_3_grams], word, word_count)

    def get_suggested_words(self, query):
        normalized_query = text_normalizer.normalize_sentence(query)
        suggested_words = []
        suggested_set = set()
        similar_words = []
        if normalized_query.upper() != normalized_query and normalized_query.upper() in self.inverted_index_n_grams:
            similar_words.append(normalized_query.upper())
        if normalized_query.lower() != normalized_query and normalized_query.lower() in self.inverted_index_n_grams:
            similar_words.append(normalized_query.lower())
        similar_words.extend(self.search_engine_inverted_index.find_similar_words_by_spelling(normalized_query, 0.8, all_similar_words = True))
        for word in similar_words:
            if word != normalized_query and word in self.inverted_index_n_grams and word not in suggested_set:
                suggested_set.add(word)
                suggested_words.append({"word":word, "similarity":1.0, "frequency":self.get_frequency_for_word(word), "percent_frequency":self.get_frequency_in_percent(word),\
                    "frequency_as_expression":self.get_frequency_as_expression(word)})
        try:
            if not text_normalizer.is_abbreviation(normalized_query):
                for word in self.fast_text_model.wv.most_similar(normalized_query, topn=30):
                    normalized_word = word[0]
                    if normalized_word not in suggested_set and normalized_word != normalized_query:
                        suggested_words.append({"word":normalized_word, "similarity":1.0, "frequency":self.get_frequency_for_word(normalized_word), \
                            "percent_frequency":self.get_frequency_in_percent(normalized_word), "frequency_as_expression":self.get_frequency_as_expression(word[0])})
                    if len(suggested_words) >= 20:
                        break
        except:
            print("Word %s not found in FastText model"%(query))
        return suggested_words[:20]

    def find_in_specific_dictionary(self, query, dict_to_check):
        normalized_query = text_normalizer.normalize_sentence(query)
        abbreviations_for_word = []
        if normalized_query not in dict_to_check:
            return []
        for word_expr in dict_to_check[normalized_query]:
            normalized_word = word_expr[0]
            abbreviations_for_word.append({"word":normalized_word, "coocurence":word_expr[1], "frequency":self.get_frequency_for_word(normalized_word), \
                        "percent_frequency":self.get_frequency_in_percent(normalized_word), "frequency_as_expression":self.get_frequency_as_expression(normalized_word)})
        return abbreviations_for_word

    def get_popular_expressions(self, query):
        return self.find_in_specific_dictionary(query, self.popular_expressions)[:20]

    def get_abbreviations_for_word(self, query):
        return self.find_in_specific_dictionary(query, self.sorted_resolved_abbreviations)

    def get_word_expressions_for_abbreviation(self, query):
        return self.find_in_specific_dictionary(query, self.sorted_words_to_abbreviations)


