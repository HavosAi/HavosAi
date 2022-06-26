import sys
sys.path.append('../src')                  
from text_processing import text_normalizer
from allennlp.predictors.predictor import Predictor
import langdetect
import re
import os
from os import listdir
from os.path import isfile, join
import uuid
import pickle
import nltk

predictor = Predictor.from_path("https://s3-us-west-2.amazonaws.com/allennlp/models/srl-model-2018.05.25.tar.gz")

class SimpleCacheContext:
    def __init__(self, cache_folder):
        self._cache_folder = cache_folder
        os.makedirs(cache_folder, exist_ok=True)
        self.cache_map = {}
        self._total_requests = 0
        self._total_hits = 0
        self.additional_map = {}
        if self._cache_folder is not None:
            self.init_cache_from_folder()

    def init_cache_from_folder(self):
        files_in_folder = [join(self._cache_folder, f) for f in listdir(self._cache_folder) if isfile(join(self._cache_folder, f))]
        for file_name in files_in_folder:
            with open(file_name, 'rb') as f:
                new_map = pickle.load(f)
                self.cache_map.update(new_map)
        print(f"Finish loading cache for folder {self._cache_folder}, total {len(files_in_folder)} files, map size is {len(self.cache_map)}")

    def search_in_cache(self, key):
        self._total_requests += 1
        if key not in self.cache_map:
            return None
        self._total_hits += 1
        return self.cache_map[key]


    def print_statistics(self):
        print(f"Chache hit = {0 if self._total_requests == 0 else self._total_hits / (self._total_requests + 0.0)}")


    def add_in_dictionary(self, key, val):
        if key in self.cache_map:
            return
        self.cache_map[key] = val
        self.additional_map[key] = val

    def save_additional_data(self):
        if len(self.additional_map) == 0:
            return
        write_path = join(self._cache_folder, str(uuid.uuid4().hex))
        with open(write_path, 'wb') as f:
            pickle.dump(self.additional_map, f)
        print(f"Write file {write_path}")
        self.additional_map = {}



class IntervectionContextsFromPageExtractor:
    def __init__(self, text, intervention_list, intervation_translation_map, extend_not_english=False, my_map_cache=None):
        self._text = text
        self._intervention_list = intervention_list
        self._extends_not_english = extend_not_english
        self._intervation_translation_map = intervation_translation_map
        self.map_cache = my_map_cache

    def save_to_cache(self):
        if self.map_cache is not None:
            self.map_cache.save_additional_data()
            self.print_statistics()

    def join_several_sentences(self, sentences, idx, num_sent=5):
        all_sentences = []
        number_sentences = len(sentences[idx-2:idx])
        all_sentences.extend(sentences[(idx-2):(idx+1)])
        all_sentences.extend(sentences[(idx+1):(idx+num_sent-number_sentences)])
        return " ".join(all_sentences)

    def extender_generator(self):
        cur_text = self._text
        cur_lang = 'NO'
        try:
            cur_lang = langdetect.detect(cur_text)
        except:
            pass
        if cur_lang != 'en':
            print("Page is not english")
        sentences = nltk.sent_tokenize(cur_text)
        for idx, sentence in enumerate(sentences):
            #cur_text_split = text_normalizer.split_sentence_to_parts(sentence)
            several_sentences = self.join_several_sentences(sentences, idx)
            normalized_sentence = text_normalizer.normalize_sentence(sentence)
            for intervention in self._intervention_list:
                intervention_in_english = intervention
                if intervention in self._intervation_translation_map and self._intervation_translation_map[intervention] != intervention:
                    intervention_in_english = self._intervation_translation_map[intervention]

                if intervention in normalized_sentence:
                    not_found_in_parts = False
                    for cur_text in [sentence]:
                        cur_text_normalized = text_normalizer.normalize_sentence(cur_text)
                        if intervention in cur_text_normalized:
                            print(".", end='')
                            not_found_in_parts = True

                            result_text = intervention_in_english
                            if intervention in self._intervation_translation_map and self._intervation_translation_map[intervention] != intervention:
                                result_text = intervention_in_english
                            
                            if cur_lang == 'en' and intervention_in_english == intervention:
                                result_text = extract_part_with_intervention_from_text(intervention, cur_text, self.map_cache)
                            yield (intervention_in_english, result_text, sentence, several_sentences)
                    if not not_found_in_parts:
                        yield (intervention_in_english, intervention_in_english, sentence, several_sentences)
                    

def extract_part_with_intervention_from_text(intervention, unnormalized_text, map_cache=None):
    if map_cache is not None:
        ans = map_cache.search_in_cache((intervention, unnormalized_text))
        if ans is not None:
            return ans
    ans = None
    result = predictor.predict(sentence=unnormalized_text)
    #print(intervention, result)
    if "verbs" in result:
        all_srl = set()
        for description in result["verbs"]:
            all_srl.add(description["description"])
        best_fit_set = set()
        sentence = unnormalized_text        
        best_fit = sentence.strip() #text_normalizer.normalize_sentence(sentence)
        for parsed_sent in all_srl:
            splited_srl = parsed_sent.replace(']','[').split('[')
            for subpart in re.findall(r"\[[\w\d]+: .*?\]", parsed_sent):
                subpart = re.search(r"\[[\w\d]+: (.*?)\]", subpart).group(1)
                normalized_subpart = subpart.strip() #text_normalizer.normalize_sentence(subpart)
                if intervention not in normalized_subpart:
                    continue
                if len(best_fit) > len(subpart) and normalized_subpart != intervention:
                    best_fit = normalized_subpart
        #print(intervention, '\t', best_fit)
        #if len(best_fit) < 100:
        #    ans = best_fit
        #else:
        #    ans = intervention
        ans = best_fit
    if ans is None:
        if len(unnormalized_text) < 100:
            ans = text_normalizer.normalize_sentence(unnormalized_text)
        else:
            ans = intervention
    if map_cache is not None:
        map_cache.add_in_dictionary((intervention, unnormalized_text), ans)
    return ans