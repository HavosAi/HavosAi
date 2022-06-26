import textdistance
from text_processing import text_normalizer
import pickle
import re
import os
import pickle
from time import time

class SearchEngineInsensitiveToSpelling:
    
    def __init__(self, filter_word_list = [], abbreviation_folder = "../model/abbreviations_dicts", load_abbreviations = False, symbols_count = 3):
        self.dictionary_by_first_letters = {}
        self.id2docArray = []
        self.newId = 0
        self.total_articles_number = 0
        self.symbols_count = symbols_count
        self._abbreviations_resolver = None
        self.load_abbreviations = load_abbreviations
        if self.load_abbreviations:
            self._abbreviations_resolver.load_model(abbreviation_folder)

    def calculate_abbreviations_count_docs(self):
        docs_with_abbreviations = {}
        for abbr in self._abbreviations_resolver.resolved_abbreviations:
            docs_found_for_abbr = self.find_articles_with_keywords([abbr], 1.0, extend_with_abbreviations=False)[0][1]
            docs_resolved = set()
            for abbr_meaning in self._abbreviations_resolver.resolved_abbreviations[abbr]:
                docs_for_abbr_meaning = self.find_articles_with_keywords([abbr_meaning], 0.92, extend_with_abbreviations=False)[0][1]
                for docId in docs_found_for_abbr.intersection(docs_for_abbr_meaning):
                    if docId not in docs_with_abbreviations:
                        docs_with_abbreviations[docId] = {}
                    if abbr not in docs_with_abbreviations[docId]:
                        docs_with_abbreviations[docId][abbr] = []
                    docs_with_abbreviations[docId][abbr].append(abbr_meaning)
                docs_resolved = docs_resolved.union(docs_for_abbr_meaning)
            for docId in docs_found_for_abbr - docs_resolved:
                if docId not in docs_with_abbreviations:
                    docs_with_abbreviations[docId] = {}
                if abbr not in docs_with_abbreviations[docId]:
                    docs_with_abbreviations[docId][abbr] = []
                docs_with_abbreviations[docId][abbr].append(self._abbreviations_resolver.sorted_resolved_abbreviations[abbr][0][0])
        for docId in docs_with_abbreviations:
            for word in docs_with_abbreviations[docId]:
                if len(docs_with_abbreviations[docId][word]) > 1:
                    sorted_abbr = sorted([(w, self._abbreviations_resolver.resolved_abbreviations[word][w])for w in docs_with_abbreviations[docId][word]],key = lambda x: x[1], reverse =True)
                    docs_with_abbreviations[docId][word] = [sorted_abbr[0][0]]
        for docId in docs_with_abbreviations:
            for word in docs_with_abbreviations[docId]:
                abbr_meanings = set()
                for abbr_meaning in docs_with_abbreviations[docId][word]:
                    abbr_meanings.add(re.sub(r"\bprogramme\b", "program", abbr_meaning))
                    abbr_meanings.add(re.sub(r"\bprogram\b", "programme", abbr_meaning))
                docs_with_abbreviations[docId][word] = list(abbr_meanings)
        self.abbreviations_count_docs = {}
        for i in docs_with_abbreviations:
            for key in docs_with_abbreviations[i]:
                if key not in self.abbreviations_count_docs:
                    self.abbreviations_count_docs[key] = {}
                for meaning in docs_with_abbreviations[i][key]:
                    if meaning not in self.abbreviations_count_docs[key]:
                        self.abbreviations_count_docs[key][meaning] = set()
                    self.abbreviations_count_docs[key][meaning].add(i)

    def save_model(self, folder="../model/search_index"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        pickle.dump([self.dictionary_by_first_letters, self.total_articles_number, self.abbreviations_count_docs if self.load_abbreviations else {}], open(os.path.join(folder, "search_index.pickle"),"wb"))

    def load_model(self, folder="../model/search_index"):
        self.dictionary_by_first_letters, self.total_articles_number, self.abbreviations_count_docs = pickle.load(open(os.path.join(folder, "search_index.pickle"),"rb"))
    
    def create_inverted_index(self, texts, continue_adding = False):
        if continue_adding:
            self.total_articles_number += len(texts)
            self.unshrink_memory(set)
        else:
            self.total_articles_number = len(texts)
        for i in range(len(texts)):
            text_words = text_normalizer.get_stemmed_words_inverted_index(texts[i])
            for j in range(len(text_words)):
                self.add_item_to_dict(text_words[j], i)
                if j != len(text_words) - 1:
                    word_expression = text_words[j] + " " + text_words[j+1]
                    self.add_item_to_dict(word_expression, i)
        self.shrink_memory()
        if self.load_abbreviations:
            self.calculate_abbreviations_count_docs()

    def shrink_memory(self, operation = list):
        for i in range(len(self.id2docArray)):
            self.id2docArray[i] = operation(self.id2docArray[i])
        return 
        for key in self.dictionary_by_first_letters:
            if len(key) < self.symbols_count:
                self.dictionary_by_first_letters[key] = operation(self.dictionary_by_first_letters[key])
            else:
                for word in self.dictionary_by_first_letters[key]:
                    self.dictionary_by_first_letters[key][word] = operation(self.dictionary_by_first_letters[key][word])
    
    def add_item_to_dict(self, word, docId):
        if len(word) == 0:
            return
        if len(word) < self.symbols_count:
            if word not in self.dictionary_by_first_letters:
                self.dictionary_by_first_letters[word] = self.newId 
                self.newId += 1
                self.id2docArray.append(set())
            self.id2docArray[self.dictionary_by_first_letters[word]].add(docId)
            return
        if word[:self.symbols_count] not in self.dictionary_by_first_letters:
            self.dictionary_by_first_letters[word[:self.symbols_count]] = {}
        if word not in self.dictionary_by_first_letters[word[:self.symbols_count]]:
            self.dictionary_by_first_letters[word[:self.symbols_count]][word] = self.newId
            self.newId += 1
            self.id2docArray.append(set())
        self.id2docArray[self.dictionary_by_first_letters[word[:self.symbols_count]][word]].add(docId)

    def get_articles_by_word(self, word):
        try:
            if len(word) < self.symbols_count:
                return self.dictionary_by_first_letters[word]
        except:
            return 0
        try:
            if len(word) >= self.symbols_count:
                return self.dictionary_by_first_letters[word[:self.symbols_count]][word]
        except:
            return 0
        return 0
                
    def find_similar_words_by_spelling(self, word, threshold = 0.9, all_similar_words = False):
        time_total = time()
        stemmed_word = " ".join(text_normalizer.get_stemmed_words_inverted_index(word))
        stemmed_word = word if len(stemmed_word) < self.symbols_count else stemmed_word
        words = set([word, stemmed_word])
        if threshold >= 0.99 or len(stemmed_word) < self.symbols_count:
            return words
        words.add(re.sub(r"\bprogramme\b", "program", word))
        words.add(re.sub(r"\bprogram\b", "programme", stemmed_word))
        intial_words = words
        try:
            articles_count = len(self.get_articles_by_word(stemmed_word))
            for dict_word in self.dictionary_by_first_letters[word[:self.symbols_count]]:
                if all_similar_words or (articles_count == 0 or len(self.get_articles_by_word(dict_word)) < 4*articles_count):
                    for w in intial_words:
                        if textdistance.levenshtein.normalized_similarity(dict_word, w) >= threshold:
                            words.add(dict_word)
        except:
            pass
        z_s_replaced_words = set()
        for word in words:
            z_s_replaced_words = z_s_replaced_words.union(text_normalizer.replaced_with_z_s_symbols_words(word, self))
        #print("Processed spelling ", time() - time_total)
        return words.union(z_s_replaced_words)
    
    def find_keywords(self, stemmed_words):
        keywords = []
        if len(stemmed_words) > 2:
            for i in range(len(stemmed_words) - 1):
                keywords.append(stemmed_words[i] + " " + stemmed_words[i+1])
        else:
            keywords.append(" ".join(stemmed_words))
        return keywords
    
    def extend_query(self, query):
        words = query.split()
        prev_set = self.find_similar_words_by_spelling(words[0])
        for i in range(1, len(words)):
            new_set = set()
            for word in self.find_similar_words_by_spelling(words[i]):
                for prev_exp in prev_set:
                    new_set.add(prev_exp + " " + word)
            prev_set = new_set
        return prev_set

    def generate_subexpressions(self, expression):
        words = expression.split()
        generated_words = set()
        for i in range(len(words)):
            word = words[i]
            generated_words.add(word)
            for j in range(i+1, len(words)):
                word = word + " " + words[j]
                generated_words.add(word)
        return generated_words

    def has_meaning_for_abbreviation(self, abbr_meanings, dict_to_check):
        return len(abbr_meanings.intersection(set([w[0] for w in dict_to_check]))) > 0

    def extend_with_abbreviations(self, query, dict_to_check, extend_abbr_meanings = ""):
        abbr_meanings = set([w.strip() for w in extend_abbr_meanings.split(";")])
        new_queries = set([query])
        subexpressions = self.generate_subexpressions(query)
        for expr in subexpressions:
            if expr in dict_to_check:
                if self.has_meaning_for_abbreviation(abbr_meanings, dict_to_check[expr]):
                    for word,cnt in dict_to_check[expr]:
                        if expr in word:
                            continue
                        if word in abbr_meanings:
                            new_query = re.sub(r"\b%s\b"%expr,  word, query)
                            if new_query not in new_queries:
                                new_queries = new_queries.union(self.extend_with_abbreviations(new_query, dict_to_check, extend_abbr_meanings))
                else:
                    for word,cnt in dict_to_check[expr]:
                        if expr in word or (len(dict_to_check[expr]) > 1 and cnt < 15):
                            continue
                        new_query = re.sub(r"\b%s\b"%expr,  word, query)
                        if new_query not in new_queries:
                            new_queries = new_queries.union(self.extend_with_abbreviations(new_query, dict_to_check, extend_abbr_meanings))
        return new_queries

    def extend_query_with_abbreviations(self, query, extend_with_abbreviations, extend_abbr_meanings=""):
        if not extend_with_abbreviations:
            return set()
        normalized_key = text_normalizer.normalize_text(query)
        extended_queries = set()
        extended_queries = extended_queries.union(self.extend_with_abbreviations(normalized_key, self._abbreviations_resolver.sorted_resolved_abbreviations, extend_abbr_meanings)) if extend_with_abbreviations else extended_queries
        new_extended_queries = extended_queries
        if extend_with_abbreviations:
            for new_query in extended_queries:
                new_extended_queries = new_extended_queries.union(self.extend_with_abbreviations(new_query, self._abbreviations_resolver.sorted_words_to_abbreviations))
        return new_extended_queries

    def get_article_with_special_abbr_meanings(self, query, abbr_meanings):
        if abbr_meanings.strip() == "":
            return set()
        docs_with_abbreviations = set()
        first_assignment = True
        for abbr_meaning in abbr_meanings.split(";"):
            abbr_meaning = abbr_meaning.strip()
            if abbr_meaning not in self._abbreviations_resolver.sorted_words_to_abbreviations:
                continue
            for word,cnt in self._abbreviations_resolver.sorted_words_to_abbreviations[abbr_meaning]:
                if re.search(r"\b%s\b"%word, query) != None and word in self.abbreviations_count_docs and abbr_meaning in self.abbreviations_count_docs[word]:
                    if first_assignment:
                        docs_with_abbreviations = docs_with_abbreviations.union(self.abbreviations_count_docs[word][abbr_meaning]) 
                        first_assignment = False
                    else:
                        docs_with_abbreviations = docs_with_abbreviations.intersection(self.abbreviations_count_docs[word][abbr_meaning])
        return docs_with_abbreviations

    
    def find_articles_with_keywords(self, key_words, threshold = 0.9, extend_query = False, extend_with_abbreviations = False, extend_abbr_meanings = ""):
        articles_with_keywords = []
        total_articles = 0
        time_start = time()
        time_total = time()
        for key in key_words:
            normalized_key = text_normalizer.normalize_text(key)
            extended_queries = self.extend_query(normalized_key) if extend_query else set([normalized_key])
            extended_queries = extended_queries.union(self.extend_query_with_abbreviations(key,extend_with_abbreviations, extend_abbr_meanings))
            #print("Extension ", time()-time_start)
            time_start = time()
            for query in extended_queries:
                first_assignment = True
                articles =0
                for key_word in self.find_keywords(text_normalizer.get_stemmed_words_inverted_index(query)):
                    sim_word_articles = 0
                    for sim_word in self.find_similar_words_by_spelling(key_word, threshold):
                        sim_word_articles += self.get_articles_by_word(sim_word)
                    if first_assignment:
                        articles = sim_word_articles 
                        first_assignment = False
                    else:
                        articles = min(articles, sim_word_articles)
                docs_with_abbreviations = self.get_article_with_special_abbr_meanings(query, extend_abbr_meanings)
                if len(docs_with_abbreviations) == 0:
                    total_articles += articles
                else:
                    total_articles += max(articles, len(docs_with_abbreviations))
                #print("One query ", time() - time_start)
                time_start = time()
        articles_with_keywords.append((key_words[0], total_articles))
        #print("Time total ", time() - time_total)
        return articles_with_keywords