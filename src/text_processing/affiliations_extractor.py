from utilities import excel_reader, excel_writer
from text_processing import text_normalizer
from utilities import utils
from time import time
import re
import spacy
import os

class AffiliationsExtractor:

    def __init__(self, ner_affiliation_extraction_model="../model/affiliation-extr-1000-74_iter"):
        self.mapping_clipped_words = self.load_remappings('../data/map_clipped_words.xlsx', "word", "mapping_word")
        self.mapping_countries = self.load_remappings('../data/countries_affiliation_remapping.xlsx', "Raw_country", "Country")
        self.univ_words = ["univ", "inst", "college", "academy", "r&d", "foundation", "research center", "hochschul", \
                  "centre", "center", "organis", "dept", "depart", "school", "research", "division", \
                 "association", "program", "project"]
        self.address_words = ["street", "avenue", "road", "place", "circle", "rue", "area", "drive", "boulevard", "crescent"]
        self.nlp_model = spacy.load("en_core_web_md")
        self.univ_raw_words_remapped = {}
        self.countries_used_for_affilaition = set()
        if ner_affiliation_extraction_model:
            self.ner_model_affil = spacy.load(ner_affiliation_extraction_model)

    def create_dictionary_for_univ_words(self, folder_with_files):
        words_found = {}
        for file in os.listdir(folder_with_files):
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_files, file))
            for i in range(len(df)):
                for w in self.remove_articles(df["affiliation"].values[i].lower()).split():
                    w = self.normalize_for_comparing(w)
                    for key_ in self.univ_words:
                        if w.startswith(key_):
                            if w not in words_found:
                                words_found[w] = 0
                            words_found[w] += 1
                            break
        words_found_remapped = {}
        for w in self.univ_words:
            top_word = ""
            top_freq = 0
            for word in words_found:
                if word.startswith(w) and words_found[word] > top_freq:
                    top_word = word
                    top_freq = words_found[word]
            if not top_word:
                continue
            for word in words_found:
                if word.startswith(w):
                    words_found_remapped[word] = w
        return words_found_remapped

    def find_countries_found_in_affilaitions(self, folder_with_files):
        countries_used_for_affilaition = set()
        for file in os.listdir(folder_with_files):
            start_time = time()
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_files, file))
            for i in range(len(df)):
                for aff in df["affiliation"].values[i].split(";"):
                    if len(aff.split(",")) > 1:
                        country_name = self.normalize_for_comparing(
                            self.remove_articles(self.clean_from_numbers(aff.split(",")[-1])))
                        if country_name:
                            countries_used_for_affilaition.add(country_name)
        return countries_used_for_affilaition

    def load_remappings(self, file_or_folder, column_raw, column_mapped):
        mapping_words = {}
        files = [file_or_folder]
        if os.path.isdir(file_or_folder):
            files = [os.path.join(file_or_folder, file) for file in os.listdir(file_or_folder)]
        for file in files:
            map_df = excel_reader.ExcelReader().read_df_from_excel(file)
            for i in range(len(map_df)):
                mapping_words[map_df[column_raw].values[i]] = map_df[column_mapped].values[i]
        return mapping_words

    def get_rank(self, sentence, default_rank = 100):
        for idx, word in enumerate(self.univ_words):
            if word in sentence.lower():
                return idx
        return default_rank

    def get_institution_name(self, affiliation_parts):
        affiliation_parts_filtered = []
        first_part = affiliation_parts[0] if not re.search(r"\d+", affiliation_parts[0]) else ""
        for affil_part in affiliation_parts:
            is_address_part = False
            for address_word in self.address_words:
                if address_word in affil_part.lower():
                    is_address_part = True
                    break
            if not is_address_part:
                affiliation_parts_filtered.append(affil_part)
        for word in self.univ_words:
            for affil_part in affiliation_parts_filtered:
                if word in affil_part.lower():
                    return affil_part
        return first_part

    def fix_clipping(self, sentence):
        for word in self.mapping_clipped_words:
            sentence = re.sub(r"\b%s\.|\b%s\b" %(word, word), self.mapping_clipped_words[word], sentence, flags=re.IGNORECASE)
        sentence = re.sub(r"\s*&\s*", " & ", sentence)
        sentence = re.sub(r"\s*of(?=[A-Z]\w+)", " of ", sentence)
        return sentence

    def remove_articles(self, sentence):
        for key_word in ["a", "the"]:
            sentence = re.sub(r"\b%s(?!(\s*&)|\.)\b" % key_word, " ", sentence, flags=re.IGNORECASE)
        sentence = re.sub(r"[\-\.\!\"#\$%\'\(\)\*\+,/:;<>=\?@\[\]\\\\^_`\{\}|~®]+", " ", sentence).strip()
        return re.sub(r"\s+", " ", sentence).strip()

    def remove_brackets(self, sentence):
        res = sentence
        if re.sub(r"\(.*?\)", "", sentence).strip():
            res = re.sub(r"\(.*?\)", "", sentence).strip()
        return re.sub(r"\s+", " ", res.replace("(", "").replace(")", "")).strip()

    def clean_from_numbers(self, word_phrase):
        punctuation_marks_plus_numbers = r"[\-\.\!\"#\$%\'\(\)\*\+,/:;<>=\?@\[\]\\\\^_`\{\}|~\d]+"
        word_phrase_cleaned = re.sub(punctuation_marks_plus_numbers, "", word_phrase).strip()
        if not word_phrase_cleaned or len(word_phrase_cleaned) < 2:
            return ""
        return re.sub(r"\d+", "", word_phrase).strip()

    def merge_one_letter_abbreviations(self, word_phrase):
        old_phrase = word_phrase
        while True:
            word_phrase = re.sub(r"\b([A-Z]+)\s+([A-Z]+)\b", r"\g<1>\g<2>", word_phrase)
            if old_phrase == word_phrase:
                break
            old_phrase = word_phrase
        return word_phrase

    def replace_with_freq_word(self, word_phrase):
        new_words = []
        for w in word_phrase.replace(",", "").split():
            if w in self.univ_raw_words_remapped:
                new_words.append(self.univ_raw_words_remapped[w])
            else:
                new_words.append(w)
        return " ".join(new_words).strip()

    def fill_universities_by_country(self, all_affiliations):
        universities_by_country = {}
        for aff in all_affiliations:
            country_name, affiliation = "", aff
            if len(aff.split(",")) > 1:
                country_name = aff.split(",")[-1].strip()
                affiliation = ",".join(aff.split(",")[:-1]).strip()
            if country_name not in universities_by_country:
                universities_by_country[country_name] = set()
            universities_by_country[country_name].add(aff)
        return universities_by_country

    def fill_mapping_by_first_letters(self, affiliations, n_first_letters=1):
        mapping_by_first_letters = {}
        for aff in affiliations:
            aff_mapped_word = self.normalize_for_comparing(aff)
            aff_mapped_word = self.replace_with_freq_word(aff_mapped_word)
            aff_mapped_word = aff_mapped_word.lower().replace(" ", "")
            if aff_mapped_word[:n_first_letters] not in mapping_by_first_letters:
                mapping_by_first_letters[aff_mapped_word[:n_first_letters]] = []
            mapping_by_first_letters[aff_mapped_word[:n_first_letters]].append(aff)
        return mapping_by_first_letters

    def fill_mapping_by_first_letters_with_splitting(self, affiliations, n_first_letters=1, max_number=500):
        mappings = self.fill_mapping_by_first_letters(affiliations, n_first_letters=n_first_letters)
        need_to_remap = set()
        while True:
            for key_ in need_to_remap:
                new_mapping = self.fill_mapping_by_first_letters(mappings[key_], n_first_letters=len(key_)+1)
                smaller_pieces = []
                for w in sorted(new_mapping.items(), key=lambda x:len(x[1])):
                    if len(smaller_pieces) + len(w[1]) < max_number:
                        smaller_pieces.extend(w[1])
                    else:
                        mappings[w[0]] = new_mapping[w[0]]
                mappings[key_] = smaller_pieces
            need_to_remap = set()
            for key_ in mappings:
                if len(mappings[key_]) > max_number:
                    need_to_remap.add(key_)
            if not len(need_to_remap):
                break
        return mappings

    def prepare_dict_for_renaming(self, new_mapping):
        new_key_remapped_vals = {}
        for key_ in new_mapping:
            if new_mapping[key_] not in new_key_remapped_vals:
                new_key_remapped_vals[new_mapping[key_]] = []
            new_key_remapped_vals[new_mapping[key_]].append(key_)
        names_to_rename = {}
        for remapped_val in new_key_remapped_vals:
            if "foundation" in remapped_val.lower():
                continue
            for raw_data in new_key_remapped_vals[remapped_val]:
                if "foundation" in raw_data.lower() and remapped_val.lower() in raw_data.lower():
                    names_to_rename[remapped_val] = remapped_val + " Foundation"
                    break
        return names_to_rename
        
    def remap_by_country(self, affiliation_counts_file, folder_with_mappings, n_first_letters=1, max_count_to_map=100):
        all_affiliations = self.load_remappings(affiliation_counts_file, "affiliation", "count")
        universities_by_country = self.fill_universities_by_country(all_affiliations)
        os.makedirs(folder_with_mappings, exist_ok=True)
        for country in universities_by_country:
            file_to_save = os.path.join(folder_with_mappings, "mapping_%s.xlsx" % country)
            if os.path.exists(file_to_save):
                continue
            full_new_mapping = {}
            print(country, len(universities_by_country[country]))
            t_start = time()
            mapping_by_first_letters = self.fill_mapping_by_first_letters_with_splitting(
                universities_by_country[country],
                n_first_letters=n_first_letters,
                max_number=500)
            
            for letters in mapping_by_first_letters:
                print(letters , len(mapping_by_first_letters[letters]))
                abbreviations_cache = {}
                new_mapping = {}
                list_of_words = [(expr, all_affiliations[expr]) for expr in mapping_by_first_letters[letters]]
                list_of_words = sorted(list_of_words, key = lambda x: x[1],reverse=True)
                for i in range(len(list_of_words)):
                    cur_i_aff = list_of_words[i][0]
                    if list_of_words[i][1] < max_count_to_map:
                        for j in range(0, i):
                            cur_j_aff = list_of_words[j][0]
                            if self.are_affiliations_similar(cur_i_aff, cur_j_aff, abbreviations_cache):
                                print(cur_i_aff, " $$$ ", cur_j_aff)
                                if cur_i_aff not in new_mapping:
                                    new_mapping[cur_i_aff] = cur_j_aff if cur_j_aff not in new_mapping else new_mapping[cur_j_aff]
                                break
                    if cur_i_aff not in new_mapping:
                        new_mapping[cur_i_aff] = cur_i_aff
                names_to_rename = self.prepare_dict_for_renaming(new_mapping)
                print("Names to rename ", names_to_rename)
                for key_ in new_mapping:
                    if new_mapping[key_] not in names_to_rename:
                        full_new_mapping[key_] = new_mapping[key_]
                    else:
                        full_new_mapping[key_] = names_to_rename[new_mapping[key_]]
                        print(new_mapping[key_], " ||| ", names_to_rename[new_mapping[key_]])
                print(abbreviations_cache)
                print("Time spent ", time() - t_start)
            print("All Time spent ", time() - t_start)
            
            excel_writer.ExcelWriter().save_data_in_excel(full_new_mapping.items(), ["raw_affiliation", "mapped_affiliation"], file_to_save)

    def sorted_string(self, word_exp):
        return " ".join(sorted(word_exp.split()))

    def generate_abbreviations(self, words_text, first_n_letters=2, exact=False):
        generated_words = set()
        if len(words_text) == 0:
            return set()
        words = self.generate_abbreviations(
            words_text[1:], first_n_letters=first_n_letters, exact=exact) if (len(words_text) > 1) else set([""])
        for word in words:
            if text_normalizer.is_abbreviation(words_text[0]):
                generated_words.add(word + (r"\w?" if not exact else "") + words_text[0].lower())
            else:
                for k in range(first_n_letters):
                    if words_text[0].lower() in text_normalizer.stopwords_all:
                        generated_words.add(word + (r"\w?" if not exact else "") + words_text[0][:(k+1)].lower())
                        generated_words.add(word)
                    else:
                        generated_words.add(word + (r"\w?" if not exact else "") + words_text[0][:(k+1)].lower())
        return generated_words

    def are_words_forming_abbreviations(
            self, words_text, word, words_count_to_check, word_abbr, first_n_letters=2, exact=False):
        words_text_pruned = words_text[:min(words_count_to_check, len(words_text))]
        if len(words_text_pruned) < 2:
            return ""
        for subset_abbr in self.generate_abbreviations(words_text_pruned, first_n_letters=first_n_letters, exact=exact):
            if re.match(subset_abbr, word.lower()) != None and re.match(
                    subset_abbr, word.lower()).group(0) == word.lower():
                return " ".join(reversed(words_text_pruned))
        return ""

    def find_text_for_abbreviation(self, word, text, first_n_letters=2,exact=False):
        word = word.replace(" ","")
        words_text = text.split()[::-1]
        if len(words_text) == 1:
            return ""
        word_abbr = "".join([letter+(r"\w?" if not exact else "") for letter in word.lower()])
        words_count_to_check = [len(word), len(word)+1, len(word)+2] + list(range(len(word)-1, 1, -1))
        for length_abbr in words_count_to_check:
            for offset in [0,1,2]:
                words_for_abbreviation = self.are_words_forming_abbreviations(
                    words_text[offset:], word, length_abbr, word_abbr, first_n_letters=first_n_letters,exact=exact)
                if words_for_abbreviation != "":
                    return words_for_abbreviation
        return ""

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

    def normalize_for_comparing(self, phrase, to_lower=True):
        phrase = re.sub(r"\b(and|of|&|de|for|do)\b","", phrase, flags=re.IGNORECASE)
        phrase = re.sub(r"\s+", " ", phrase).strip()
        phrase = text_normalizer.remove_accented_chars(phrase)
        if to_lower:
            phrase = phrase.lower()
        return phrase

    def filter_by_univ_words(self, phrase, additional_filter_words=["state", "limited", "incorporation",
                                                             "corporation", "company", "LLC"]):
        for filter_word in (self.univ_words + additional_filter_words):
            phrase = re.sub(r"\b%s\w*\b" % filter_word, " ", phrase, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", phrase).strip()

    def check_similarity(self, first_phrase, second_phrase, debug=False):
        if not first_phrase.strip() or not second_phrase.strip():
            return False
        first_phrase, second_phrase = first_phrase.lower(), second_phrase.lower()
        first_affil, second_affil  = self.filter_by_univ_words(first_phrase), self.filter_by_univ_words(second_phrase)
        lowered_first_affil, lowered_second_affil = first_affil.lower(), second_affil.lower()
        doc1 = self.nlp_model(first_affil)
        doc2 = self.nlp_model(second_affil)
        if debug:
            print(first_phrase)
            print(second_phrase)
            print(first_affil)
            print(second_affil)
            print(utils.normalized_levenshtein_score(first_phrase, second_phrase))
            print(utils.normalized_levenshtein_score(self.sorted_string(first_phrase), self.sorted_string(second_phrase)))
            print(utils.normalized_levenshtein_score(first_affil, second_affil))
            print(doc1.similarity(doc2))
        return (utils.normalized_levenshtein_score(first_phrase, second_phrase) >= 0.92 and utils.normalized_levenshtein_score(
                        lowered_first_affil, lowered_second_affil) >=0.85)or\
                (utils.normalized_levenshtein_score(
                    self.sorted_string(first_phrase), self.sorted_string(second_phrase)) >= 0.92 and utils.normalized_levenshtein_score(
                        lowered_first_affil, lowered_second_affil) >=0.85) or\
                (doc1.vector_norm and doc2.vector_norm and doc1.similarity(doc2) >= 0.98 and utils.normalized_levenshtein_score(
            lowered_first_affil, lowered_second_affil) > 0.8)

    def similar_geo_direct_words_match(self, first_affil, second_affil):
        words_to_match = ["north", "south", "east", "west"]
        words_first_match = set()
        words_second_match = set()
        for w in words_to_match:
            if w in first_affil.lower():
                words_first_match.add(w)
            if w in second_affil.lower():
                words_second_match.add(w)
        intersected_words = words_first_match.intersection(words_second_match)
        if len(words_first_match - intersected_words) > 0 and len(words_second_match - intersected_words) > 0:
            return False
        return True

    def similar_by_nonintersecting_words(self, first_affil, second_affil):
        old_first_affil, old_second_affil = first_affil, second_affil
        first_affil, second_affil  = self.filter_by_univ_words(first_affil), self.filter_by_univ_words(second_affil)
        first_words = set(filter(lambda x: x.strip(), first_affil.lower().split()))
        second_words = set(filter(lambda x: x.strip(), second_affil.lower().split()))
        intersected_words = first_words.intersection(second_words)
        result = utils.normalized_levenshtein_score(self.sorted_string(" ".join(first_words - intersected_words)),
                                                  self.sorted_string(" ".join(second_words - intersected_words)))
        if result < 0.4:
            if len(first_words - intersected_words) == 0 or len(second_words - intersected_words) == 0:
                return True
        return result > 0.4

    def are_affiliations_similar(self, first_affil, second_affil, abbreviations_cache, debug=False):
        if text_normalizer.is_abbreviation(",".join(first_affil.split(",")[:-1])) and text_normalizer.is_abbreviation(
            ",".join(second_affil.split(",")[:-1])):
            return first_affil.replace(" ","").strip() == second_affil.replace(" ","").strip()
        
        country_name = ""
        if len(first_affil.split(",")) > 1:
            country_name = first_affil.split(",")[-1].strip()
        
        first_affil = self.replace_with_freq_word(self.normalize_for_comparing(first_affil, to_lower=False))
        second_affil = self.replace_with_freq_word(self.normalize_for_comparing(second_affil, to_lower=False))
        
        if not self.similar_geo_direct_words_match(first_affil.lower(), second_affil.lower()):
            return False
        if not self.similar_by_nonintersecting_words(first_affil.lower(), second_affil.lower()):
            return False
        
        result = self.check_similarity(first_affil, second_affil, debug=debug)
        if result:
            return True
        
        for first_word, second_word in [(first_affil, second_affil), (second_affil, first_affil)]:
            for abbr in self.generate_subexpressions(
                    " ".join([w for w in first_word.split() if text_normalizer.is_abbreviation(w) and w not in ["USA", "UK"]])):
                try:
                    if len(abbr.strip()) < 2:
                        continue
                    res = ""
                    if (abbr, country_name) in abbreviations_cache:
                        res = abbreviations_cache[(abbr, country_name)]
                    else:
                        res = self.find_text_for_abbreviation(abbr, second_word, first_n_letters=1,exact=True)
                    
                    if res:
                        abbreviations_cache[(abbr, country_name)] = res
                        first_word_replaced = first_word.replace(abbr, res)
                        second_word_replaced = second_word.replace(abbr, res)
                        if self.check_similarity(first_word_replaced, second_word_replaced, debug=debug):
                            return True
                except:
                    print("Error ", abbr, " $$$ ", first_word, " $$$ ", second_word)
                    pass
        return False

    def preprocess_affiliations(self, raw_affiliations):
        processed_affiliations = []
            
        for affilaition in raw_affiliations.split(";"):
            affilaition = self.fix_clipping(affilaition)
            processed_affiliation = ""

            if len(affilaition.split(",")) > 1:
                country_name = affilaition.split(",")[-1]
                country_name = re.sub(r"\d+", "", country_name).strip()
                if country_name.strip() in self.mapping_countries:
                    country_name = self.mapping_countries[country_name.strip()]
                country_name = self.remove_articles(self.clean_from_numbers(text_normalizer.to_camel_case(country_name))).strip()


                institution_part = self.get_institution_name(
                    [r.strip() for r in affilaition.split(",") if r.strip()])
                if institution_part:
                    institution_part = text_normalizer.to_camel_case(institution_part)

                all_parts = []
                for aff in self.ner_model_affil(affilaition).ents:
                    aff = aff.text.strip()
                    if aff:
                        all_parts.append((aff, self.get_rank(aff, default_rank=100)))
                if institution_part.strip():
                    all_parts.append((institution_part, self.get_rank(institution_part, default_rank=101)))
                all_parts = sorted(all_parts, key=lambda x: (x[1], len(x[0])))
                if all_parts:
                    aff = self.remove_brackets(all_parts[0][0])
                    if country_name == "USA":
                        aff = re.sub(r"\bUC\b", "University of California", aff)
                    aff = self.remove_articles(self.clean_from_numbers(text_normalizer.to_camel_case(aff))).strip()
                    processed_affiliation = aff if not country_name else (aff + ", " + country_name)
            else:
                processed_affiliation = self.remove_articles(
                    self.clean_from_numbers(text_normalizer.to_camel_case(affilaition))).strip()
            processed_affiliation = re.sub(r"\b in \w+\b|\b at \w+\b", "", processed_affiliation)
            processed_affiliation = re.sub(r"^(and\b|\&)", "", processed_affiliation).strip()
            processed_affiliation = self.merge_one_letter_abbreviations(processed_affiliation)

            if processed_affiliation.strip() and not processed_affiliation.strip().startswith(","):
                processed_affiliations.append(processed_affiliation)
        return processed_affiliations

    def extract_affiliations(self, folder_with_files, folder_with_processed,
                             affiliation_counts_file,
                             processed_column_name="processed_affiliation",
                             column_name_to_extract="affiliation"):
        os.makedirs(folder_with_processed, exist_ok=True)
        affiliation_counts = {}
        if os.path.exists(affiliation_counts_file):
            affiliation_counts = self.load_remappings(affiliation_counts_file, "affiliation", "count")
        for file in os.listdir(folder_with_files):
            start_time = time()
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_files, file))
            df[processed_column_name] = ""
            for i in range(len(df)):
                
                processed_affiliations = self.preprocess_affiliations(df[column_name_to_extract].values[i])
                
                df[processed_column_name].values[i] = processed_affiliations
                
                for processed_affiliation in processed_affiliations:
                    if processed_affiliation not in affiliation_counts:
                        affiliation_counts[processed_affiliation] = 0
                    affiliation_counts[processed_affiliation] += 1

            print("Spent time ", time() - start_time)
            excel_writer.ExcelWriter().save_df_in_excel(df, os.path.join(folder_with_processed, file))
        excel_writer.ExcelWriter().save_data_in_excel(affiliation_counts.items(), ["affiliation", "count"], affiliation_counts_file)

    def extract_corporate_author(self, folder_with_files, folder_with_processed,
                                 affiliation_counts_file,
                                 processed_column_name="processed_corporate_author",
                                 column_name_to_extract="corporate_author"):
        os.makedirs(folder_with_processed, exist_ok=True)
        affiliation_counts = {}
        if os.path.exists(affiliation_counts_file):
            affiliation_counts = self.load_remappings(affiliation_counts_file, "affiliation", "count")
        for file in os.listdir(folder_with_files):
            start_time = time()
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_files, file))
            df[processed_column_name] = ""
            for i in range(len(df)):
                
                raw_corporate_authors = []
                for aff in df[column_name_to_extract].values[i].split(";"):
                    country_name = ""
                    parts = [val.strip() for val in aff.split(",") if val.strip()]
                    if parts:
                        first_part_normalized = self.normalize_for_comparing(self.remove_articles(self.clean_from_numbers(parts[0])))
                        if first_part_normalized in self.countries_used_for_affilaition:
                            country_name = self.remove_articles(self.clean_from_numbers(text_normalizer.to_camel_case(parts[0]))).strip()
                            parts = parts[1:]            
                    if parts:
                        first_part_normalized = self.normalize_for_comparing(self.remove_articles(self.clean_from_numbers(parts[-1])))
                        if first_part_normalized in self.countries_used_for_affilaition:
                            country_name = self.remove_articles(self.clean_from_numbers(text_normalizer.to_camel_case(parts[-1]))).strip()
                            parts = parts[:-1]
                    affiliation = ",".join(parts)
                    if country_name:
                        affiliation = affiliation + ", " + country_name
                    raw_corporate_authors.append(affiliation)
                
                processed_affiliations = self.preprocess_affiliations(";".join(raw_corporate_authors))
                
                df[processed_column_name].values[i] = processed_affiliations
                
                for processed_affiliation in processed_affiliations:
                    if processed_affiliation not in affiliation_counts:
                        affiliation_counts[processed_affiliation] = 0
                    affiliation_counts[processed_affiliation] += 1

            print("Spent time ", time() - start_time)
            excel_writer.ExcelWriter().save_df_in_excel(df, os.path.join(folder_with_processed, file))
        excel_writer.ExcelWriter().save_data_in_excel(affiliation_counts.items(), ["affiliation", "count"], affiliation_counts_file)

    def extract_affiliations_and_remap(self, folder_with_files, folder_with_processed,
                                       folder_with_mapped_affiliations, affiliation_counts_file,
                                       column_affiliation_mappings={"column_name_to_extract":"affiliation",
                                                                    "processed_column_name": "processed_affiliation"},
                                       column_corporate_author_mappings={"column_name_to_extract":"corporate_author",
                                                                         "processed_column_name": "processed_corporate_author"}):
        # Main processing function
        self.univ_raw_words_remapped = self.create_dictionary_for_univ_words(folder_with_files)
        self.countries_used_for_affilaition = self.find_countries_found_in_affilaitions(folder_with_files)
        if column_affiliation_mappings:
            self.extract_affiliations(folder_with_files, folder_with_processed,
                                      affiliation_counts_file,
                                      processed_column_name=column_affiliation_mappings["processed_column_name"],
                                      column_name_to_extract=column_affiliation_mappings["column_name_to_extract"])
        if column_corporate_author_mappings:
            self.extract_corporate_author(folder_with_files, folder_with_processed,
                                          affiliation_counts_file,
                                          processed_column_name=column_corporate_author_mappings["processed_column_name"],
                                          column_name_to_extract=column_corporate_author_mappings["column_name_to_extract"])
        self.remap_by_country(affiliation_counts_file, folder_with_mapped_affiliations, n_first_letters=3)

    def map_affilations_from_clustered_affiliations(self, folder_with_files, folder_with_processed, folder_with_remapped_affilations,
                                                    column_affiliation_mappings={"column_name_to_map":"processed_affiliation",
                                                                    "processed_column_name": "affiliation_processed"},
                                                    column_corporate_author_mappings={"column_name_to_map":"processed_corporate_author",
                                                                         "processed_column_name": "corporate_author_processed"}):
        # Use the function for remapping extracted affilations via mappings from "remap_by_country" or manually fixed
        mappings_affiliations = self.load_remappings(folder_with_remapped_affilations, "raw_affiliation", "mapped_affiliation")
        os.makedirs(folder_with_processed, exist_ok=True)
        for file in os.listdir(folder_with_files):
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder_with_files, file))
            for remapping in [column_affiliation_mappings, column_corporate_author_mappings]:
                if remapping:
                    df[remapping["processed_column_name"]] = ""
            for remapping in [column_affiliation_mappings, column_corporate_author_mappings]:
                if remapping:
                    for i in range(len(df)):
                        new_affiliations = []
                        for aff in df[remapping["column_name_to_map"]].values[i]:
                            if aff not in mappings_affiliations:
                                print("Error affiliation is not found: ", aff)
                                new_affiliations.append(aff)
                            else:
                                new_affiliations.append(mappings_affiliations[aff])
                        df[remapping["processed_column_name"]].values[i] = new_affiliations
            excel_writer.ExcelWriter().save_df_in_excel(df, os.path.join(folder_with_processed, file))

