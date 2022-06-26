from langdetect import detect
import unicodedata
import nltk
import re
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import pycountry
import pandas as pd
import textdistance

stop_word_units = ["kg", "g", "mg", "ml", "l", "s", "ms", "km", "mm","la","en","le","de","et","los","une", "un", "del","i","ii","iii","iv","A","per","also","ha","cm","non","ton","etc","el"]
stopwords_all = set(nltk.corpus.stopwords.words("english") + stop_word_units)
lemma_exception_words = {"assess":"assess", "assesses":"assess"}
lmtzr = WordNetLemmatizer()

def get_year(value):
    new_val = 0
    try:
        new_val = int(value)
    except:
        pass
    return new_val

def get_only_english_text(raw_text, separator):
    text = []
    for text_part in raw_text.split(separator):
        try:
            if text_part.strip()  != "" and detect(text_part.lower()) == "en":
                text.append(text_part)
        except:
            print(text_part)
            text.append(text_part)
    new_text = separator.join(text).strip()
    return  new_text if new_text != "" else raw_text

def update_title_and_abstract_only_english(df, abstr_separator = ";", title_separator = ";"):
    for i in range(len(df)):
        lower_abstract = df["abstract"].values[i].lower()
        lower_title = df["title"].values[i].lower()
        if abstr_separator in df["abstract"].values[i] and detect(lower_abstract) != "en":
            print(i)
            print(df["abstract"].values[i])
            df["abstract"].values[i] = get_only_english_text(df["abstract"].values[i], abstr_separator)
            print(df["abstract"].values[i])
            print("######")
        if title_separator in df["title"].values[i] and detect(lower_title) != "en":
            print(i)
            print(df["title"].values[i])
            df["title"].values[i] = get_only_english_text(df["title"].values[i], title_separator)
            print(df["title"].values[i])
            print("###")
    return df

def remove_accented_chars(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return text

def get_normalized_text_with_numbers(document):
    stemmer = SnowballStemmer("english")
    lmtzr = WordNetLemmatizer()
    document = document.lower()
    words = []
    reg = re.compile("[^a-zA-Z0-9]")
    document = reg.sub(" ", document).strip()
    for word in document.split():
        if word not in stopwords_all and (len(word) > 1 or word in "0123456789"):
            lemmatized_word = lmtzr.lemmatize(word)
            stemmed_word = stemmer.stem(lemmatized_word)
            words.append(stemmed_word)
    return words  

def normalize_authors(df, column_name):
    return [author for author in df[column_name].astype(str).str.split(';').map(lambda authors: [
        a.replace('.', '').replace(',', '').replace(' ', '').strip()
        for a in authors
    ]) if author != ""]

def is_abbreviation(text):
    if text.isupper():
        return True
    if len(text) > 1 and text[-1] == "s" and text[:-1].isupper():
        return True
    return False

def normalize_abbreviation(text):
    if text[-1] == "s":
        return text[:-1]
    return text

def normalize_text(text, lower=True):
    reg = re.compile(r"[^\w\d]|\b\d+\w*\b|_")
    text = reg.sub(" ", text).strip()
    text = re.sub("\s+", " ", text)
    text = remove_accented_chars(text)
    if lower:
        new_text = ""
        for word in text.split():
            if is_abbreviation(word):
                new_text = new_text + " " + normalize_abbreviation(word)
            else:
                new_text = new_text + " " + word.lower()
        text = new_text
    return text.strip()

def remove_copyright(text):
    text = text if text.lower() != "[no abstract available]" else ""
    return re.sub("\s+"," ", re.sub("([C|c])opyright ?\.?", "", text.split("©")[0].strip().split("(c)")[0].strip().split("(C)")[0].strip()).strip(), flags=re.IGNORECASE)

def get_stemmed_words_inverted_index(doc, regex = r'\b\w+\b', to_lower = True, lemmatize_capital_words = True):
    words = []
    for w in doc.split(" "):
        list_w = re.findall(regex, w)
        for list_word in list_w: 
            if list_word in stopwords_all or re.match(r"\d+", list_word) != None:
                continue
            if is_abbreviation(list_word):
                lemmatized_word = normalize_abbreviation(list_word)
                if lemmatized_word not in stopwords_all:
                    words.append(lemmatized_word)
            else:
                if len(list_word) > 1 and list_word.lower() not in stopwords_all:
                    lemmatized_word = list_word
                    if lemmatize_capital_words:
                        lemmatized_word = lmtzr.lemmatize(list_word)
                    else:
                        lemmatized_word = lmtzr.lemmatize(list_word) if list_word[0].islower() else list_word
                    if list_word in lemma_exception_words:
                        lemmatized_word = lemma_exception_words[list_word]
                    if to_lower:
                        lemmatized_word = lemmatized_word.lower()
                    if(len(lemmatized_word) <= 1):
                        lemmatized_word = list_word
                    if lemmatized_word not in stopwords_all:
                        words.append(lemmatized_word)
    return words

def get_all_freq_words():
    freq_words = set()
    temp_df = pd.read_excel('../data/MostFrequentWords.xlsx').fillna("")
    for i in range(len(temp_df)):
        word = temp_df["Word"].values[i].lower().strip() 
        freq_words.add(word)
    return freq_words

def normalize_sentences(texts):
    sentences =[get_stemmed_words_inverted_index(normalize_text(text)) for text in texts]
    return sentences

def normalize_sentence(text):
    return " ".join(get_stemmed_words_inverted_index(normalize_text(text)))

def normalize_sentence_after_phrases(sentence):
    return [word.replace("_"," ") for word in sentence]

def normalize_country_name(country_name):
    country_name = country_name.split(',')[0].strip()
    country_name = re.sub("\s+", " ", re.sub("\(.*?\)|\[.*?\]", " ", country_name)).strip()
    return remove_accented_chars(country_name)

def build_filter_geo_points_dictionary(filename = "../data/Filter_Geo_Names.xlsx"):
    filter_word_list = []
    temp_df = pd.read_excel(filename)
    for i in range(len(temp_df)):
        filter_word_list.append(temp_df["Word"].values[i])
    return filter_word_list

def tokenize_words(text):
    return list(filter(None, re.split(r"[,;.!?:\(\)]+|\band\b|\bor\b", text)))

def are_words_glued(word, stop_word, search_engine_inverted_index):
    if " " in word or len(stop_word) == 1 or (len(word)-len(stop_word)) < 4 or len(search_engine_inverted_index.get_articles_by_word(word)) > 5:
        return False
    lemmatized_word = lmtzr.lemmatize(word[len(stop_word):])
    if lemmatized_word == "ever":
        return False
    if word[:len(stop_word)] == stop_word and len(search_engine_inverted_index.get_articles_by_word(lemmatized_word)) > 70:
        return True
    lemmatized_word = lmtzr.lemmatize(word[:-len(stop_word)])
    if word[-len(stop_word):] == stop_word and len(search_engine_inverted_index.get_articles_by_word(lemmatized_word)) > 70:
        return True
    return False

def find_glued_words(search_engine_inverted_index, big_search_engine_inverted_index):
    stop_word_for_glued_words = set(nltk.corpus.stopwords.words("english")) - set(["me","he","she","her","it","am","be","do","an",\
        "or","as","at","by","up","in","out","un","on","off","over","under","all","any","no","nor","so","don","re","ll","ve","ain","ma","shan","down"])
    exception_words = ["beforehand","profits", "hereinafter","wholesome","topics"]

    pairs_with_glued_words = {}
    for key in search_engine_inverted_index.dictionary_by_first_letters:
        if len(key) > 2:
            for word in search_engine_inverted_index.dictionary_by_first_letters[key]:
                for stop_word in stop_word_for_glued_words:
                    if word not in exception_words and are_words_glued(word, stop_word,big_search_engine_inverted_index):
                        print(stop_word, word)
                        for doc in search_engine_inverted_index.get_articles_by_word(word):
                            if doc not in pairs_with_glued_words:
                                pairs_with_glued_words[doc] = []
                            pairs_with_glued_words[doc].append((word, stop_word))
                        break
    return pairs_with_glued_words

def clean_text(text, text_to_replace, stop_word):
    while re.search(text_to_replace, text, flags=re.IGNORECASE) != None:
        old_val = re.search(text_to_replace, text, flags=re.IGNORECASE).group(0)
        if old_val.isupper():
            break
        new_val = ""
        if re.match(stop_word, old_val[:len(stop_word)], flags=re.IGNORECASE):
            new_val = old_val[:len(stop_word)] + " " + old_val[len(stop_word):]
        elif re.match(stop_word, old_val[-len(stop_word):], flags=re.IGNORECASE):
            new_val = old_val[:-len(stop_word)] + " " + old_val[-len(stop_word):]
        text = text.replace(old_val, new_val)
        print(old_val, "###",new_val,"###",text_to_replace, "###",stop_word)
    return text

def separate_glued_pairs(articles_df, search_engine_inverted_index, big_search_engine_inverted_index):
    pairs_with_glued_words = find_glued_words(search_engine_inverted_index, big_search_engine_inverted_index)
    for doc in pairs_with_glued_words:
        for pair in pairs_with_glued_words[doc]:
            articles_df["title"].values[doc] = clean_text(articles_df["title"].values[doc], pair[0],pair[1])
            articles_df["abstract"].values[doc] = clean_text(articles_df["abstract"].values[doc], pair[0],pair[1])
            articles_df["keywords"].values[doc] = clean_text(articles_df["keywords"].values[doc], pair[0],pair[1])
            articles_df["identificators"].values[doc] = clean_text(articles_df["identificators"].values[doc], pair[0],pair[1])
    return articles_df

def get_phrased_sentence(text, phrases, phrases_3gram=None):
    sentence = []
    for sent in normalize_sentences(tokenize_words(text)):
        sentence.extend(normalize_sentence_after_phrases(phrases[sent] if phrases_3gram == None else phrases_3gram[phrases[sent]]))
    return sentence

def clean_semicolon_expressions(articles_df):
    for i in range(len(articles_df)):
        text = ""
        add_short_semicolon_expressions = False
        was_changed =False
        if articles_df["abstract"].values[i] == "":
            continue
        splitted_expressions = articles_df["abstract"].values[i].split(";")
        for idx, expr in enumerate(splitted_expressions):
            if re.match(r"[\w\d -]*", expr) != None and re.match(r"[\w\d -]*", expr).group(0) == expr and len(expr.split()) < 3 and not add_short_semicolon_expressions:
                if idx < len(splitted_expressions) - 1 and splitted_expressions[idx+1].strip() != "" and splitted_expressions[idx+1].strip()[0].islower():
                    add_short_semicolon_expressions = True
                was_changed = True
            else:
                add_short_semicolon_expressions = True
            if add_short_semicolon_expressions:
                if text == "":
                    text += expr
                else:
                    text = text + ";" +expr
        if was_changed:
            articles_df["abstract"].values[i] = text.strip()
    return articles_df

def clean_semicolon_expressions_in_the_end(articles_df):
    for i in range(len(articles_df)):
        text = ""
        add_short_semicolon_expressions = False
        was_changed =False
        if articles_df["abstract"].values[i] == "":
            continue
        splitted_expressions = articles_df["abstract"].values[i].split(";")
        for idx, expr in enumerate(splitted_expressions):
            if len(expr.split()) > 3:
                if text == "":
                    text += expr
                else:
                    text = text + ";" + expr
            if expr.strip() != "" and expr.strip()[-1] == "." and idx < len(splitted_expressions) -1 and len(splitted_expressions[idx+1].split()) < 3:
                was_changed =True
                break
        if was_changed:
            articles_df["abstract"].values[i] = text
    return articles_df

def normalize_key_words(articles_df):
    articles_df["normalized_key_words"] = ""
    for i in range(len(articles_df)):
        keywords_list = articles_df["keywords"].values[i].split(";")
        keywords_list.extend(articles_df["identificators"].values[i].split(";"))
        keywords_list = [normalize_sentence(key_word).lower() for key_word in keywords_list]
        articles_df["normalized_key_words"].values[i] = [key_word for key_word in keywords_list if key_word != ""]
    return articles_df

def correct_journal_names(articles_df):
    if "journal" not in articles_df.columns:
        return articles_df
    for i in range(len(articles_df)):
        if type(articles_df["journal"].values[i]) != str:
            continue
        articles_df["journal"].values[i] = articles_df["journal"].values[i].replace("&amp;","&")
        if ";" in articles_df["journal"].values[i]:
            print(i, "###", articles_df["journal"].values[i], "###", articles_df["dataset"].values[i])
            separator_semicolon = False
            for val in articles_df["journal"].values[i].split(";"):
                if val.strip().lower().startswith("vol."):
                    separator_semicolon = True
            if separator_semicolon:
                articles_df["journal"].values[i] = articles_df["journal"].values[i].split(";")[0]
            else:
                for val in articles_df["journal"].values[i].split(";"):
                    if "," in val:
                        articles_df["journal"].values[i] = val.split(",")[0].strip()
    for i in range(len(articles_df)):
        journals = set()
        if type(articles_df["journal"].values[i]) == str:
            for journal in articles_df["journal"].values[i].split(";"):
                new_journal = journal.strip()
                if new_journal != "":
                    journals.add(new_journal)
            articles_df["journal"].values[i] = list(journals)
    return articles_df

def remove_brackets_from_authors_name(articles_df):
    if "author" not in articles_df.columns:
        return articles_df
    for i in range(len(articles_df)):
        authors = set()
        for author in articles_df["author"].values[i]:
            new_author = re.sub("\[.*?\]|\(.*?\)", "", author).strip()
            if new_author != "":
                authors.add(new_author)
        articles_df["author"].values[i] = list(authors)
    return articles_df

def contain_name(word, words_to_check):
    for w in words_to_check:
        if w in word:
            return True
    return False

def contain_full_name(word, words_to_check):
    for w in words_to_check:
        if re.search(r"\b%ss?\b"%w,word) != None:
            return True
    return False

def contain_verb_form(verb, verbs_to_check):
    for v in verbs_to_check:
        if v in verb or re.sub(r"e\b","",v) in verb:
            return True
    return False

def has_word_with_one_non_digit_symbol(word):
    for w in word.split():
        if re.search("\d",w) != None:
            word_norm = re.sub("\d","", w)
            if len(word_norm) < 2:
                return True
    return False

def are_words_similar_by_symbol_replacement(first_word, symbol, symbol_to_replace, second_word):
    if symbol in first_word and len(first_word) > 5:
        text = first_word
        while text != "":
            try:
                ind = text.rindex(symbol)
                if ind < len(first_word) - 1 and ind > 1:
                    new_word = first_word[:ind] + symbol_to_replace + first_word[ind+1:]
                    if new_word == second_word:
                        return True
                text = text[:ind]
            except:
                text = ""
    return False

def are_words_similar_by_replacing_z_s(first_word, second_word):
    return are_words_similar_by_symbol_replacement(first_word, "s","z",second_word) or are_words_similar_by_symbol_replacement(first_word, "z","s",second_word)

def are_words_similar(first_word, second_word, threshold):
    if textdistance.levenshtein.normalized_similarity(first_word, second_word) >= threshold:
        return True
    return are_words_similar_by_replacing_z_s(first_word, second_word)

def normalize_without_lowering(word_expr):
    words = []
    for word in word_expr.split():
        if word.lower() not in stopwords_all and lmtzr.lemmatize(word.lower()) not in stopwords_all:
            words.append(word)
    return " ".join(words)

def replace_string_default_values(articles_df, column_name):
    for article in range(len(articles_df)):
        if articles_df[column_name].values[article] == "":
            articles_df[column_name].values[article] = []
        else:
            articles_df[column_name].values[article] = list(articles_df[column_name].values[article])
    return articles_df

def replace_brackets_with_signs(articles_df):
    pat_set = set()
    for i in range(len(articles_df)):
        for m in re.finditer("\{.*?\}", articles_df["abstract"].values[i]):
            match_str = m.group(0)
            pat_set.add(match_str)
    dict_patterns_to_change = {}
    for pat in pat_set:
        if re.search("\w+|[%&#]",pat) != None:
            res = re.search("\w+|[%&#]",pat).group(0)
            if len(res) == 1 and res != "_":
                dict_patterns_to_change[pat] = res
        if pat not in dict_patterns_to_change:
            dict_patterns_to_change[pat] = ""
    for key in dict_patterns_to_change:
        for i in range(len(articles_df)):
            articles_df["abstract"].values[i] = articles_df["abstract"].values[i].replace(key, dict_patterns_to_change[key])
    return articles_df

def remove_html_tags(text):
    text = re.sub(r"<.+?>","",text)
    text = re.sub(r"</.+?>","",text)
    text = re.sub(r"\(\s*\)","",text)
    text = re.sub(r"\[\s*\]","",text)
    text = text.replace("&amp;","&")
    text = text.replace("&gt;",">")
    text = text.replace("&lt;","<")
    return re.sub("\s+"," ",text)

def remove_last_square_brackets(text):
    sq_brackets = re.findall(r"\[.*?\]",text)
    if len(sq_brackets) ==0:
        return text
    if len(get_stemmed_words_inverted_index(text.replace(sq_brackets[-1],"").strip())) < 2:
        return text.replace("["," ").replace("]"," ").strip()
    if len(get_stemmed_words_inverted_index(text.split(sq_brackets[-1])[1])) > 2:
        return text
    return text.replace(sq_brackets[-1],"").strip()

def remove_all_last_square_brackets_from_text(text):
    new_text = remove_last_square_brackets(text)
    while  new_text != text:
        text = new_text
        new_text = remove_last_square_brackets(text)
    return new_text

def normalize_text_columns(articles_df):
    articles_df = replace_brackets_with_signs(articles_df)
    articles_df = remove_brackets_from_authors_name(articles_df)
    articles_df = correct_journal_names(articles_df)
    articles_df = normalize_key_words(articles_df)
    articles_df = clean_semicolon_expressions(articles_df)
    articles_df = clean_semicolon_expressions_in_the_end(articles_df)
    articles_df["title"] = articles_df["title"].apply(remove_all_last_square_brackets_from_text)
    articles_df["title"] = articles_df["title"].apply(remove_html_tags)
    articles_df["abstract"] = articles_df["abstract"].apply(remove_html_tags)
    articles_df["abstract"] = articles_df["abstract"].apply(clean_text_from_commas)
    articles_df["abstract"] = articles_df["abstract"].apply(remove_copyright)
    articles_df["abstract"] = articles_df["abstract"].apply(remove_all_last_square_brackets_from_text)
    articles_df["abstract"] = articles_df["abstract"].apply(clean_text_from_commas)
    articles_df["title_norm"] = articles_df["title"].apply(normalize_text)
    articles_df["abstract_norm"] = articles_df["abstract"].apply(normalize_text)
    articles_df["key_words_norm"] = ""
    for i in range(len(articles_df)):
        articles_df["key_words_norm"].values[i] += ";".join([normalize_text(key_word) for key_word in articles_df["keywords"].values[i].replace(",",";").split(";")]) 
        identificators = ";".join([normalize_text(key_word) for key_word in articles_df["identificators"].values[i].replace(",",";").split(";")])
        if identificators.strip() != "":
            articles_df["key_words_norm"].values[i] = articles_df["key_words_norm"].values[i] + ";" + identificators
            articles_df["key_words_norm"].values[i] = ";".join(articles_df["key_words_norm"].values[i].split(";"))
    articles_df["text"] = articles_df["title_norm"] + ". " + articles_df["abstract_norm"] + ". " + articles_df["key_words_norm"].replace(";", " ; ")
    articles_df["abstract_translated"] = ""
    articles_df["title_translated"] = ""
    articles_df["keywords_translated"] = ""
    for i in range(len(articles_df)):
        articles_df["abstract_translated"].values[i] = remove_accented_chars(articles_df["abstract"].values[i])
        articles_df["title_translated"].values[i] = remove_accented_chars(articles_df["title"].values[i].lower() if articles_df["title"].values[i].isupper() else articles_df["title"].values[i])
        articles_df["keywords_translated"].values[i] = remove_accented_chars(articles_df["keywords"].values[i].lower()) + "; " + remove_accented_chars(articles_df["identificators"].values[i].lower())
        articles_df["keywords_translated"].values[i] = "; ".join(articles_df["keywords_translated"].values[i].split(";"))
    return articles_df

def replace_uppercase_words(articles_df, temp_search_engine_inverted_index, all_search_engine_inverted_index, search_engine_inverted_index, _abbreviations_resolver):
    words_set = set()
    for key in all_search_engine_inverted_index.dictionary_by_first_letters:
        if len(key) >= 2:
            words_to_process = all_search_engine_inverted_index.dictionary_by_first_letters[key] if type(all_search_engine_inverted_index.dictionary_by_first_letters[key]) == dict else [key]
            for word in words_to_process:
                if word.isupper() and not word in _abbreviations_resolver.resolved_abbreviations:
                    for w in word.split():
                        if w not in _abbreviations_resolver.resolved_abbreviations and len(w) > 1 and re.search("\d+",w) == None:
                            words_set.add(w)
    words_to_change = []
    for word in words_set:
        w_lem = lmtzr.lemmatize(word.lower())
        w_count = len(temp_search_engine_inverted_index.get_articles_by_word(w_lem))
        w_up_count = len(temp_search_engine_inverted_index.get_articles_by_word(word))
        if (w_up_count == 0 and w_count > 0) or (w_up_count > 0 and w_count/w_up_count > 3):
            words_to_change.append(word)
    for word in words_to_change:
        for article_id in search_engine_inverted_index.get_articles_by_word(word):
            articles_df["text"].values[article_id] = re.sub(r"\b%s\b"%word, word.lower(), articles_df["text"].values[article_id])
            articles_df["abstract_translated"].values[article_id] = re.sub(r"\b%s\b"%word, word.lower(), articles_df["abstract_translated"].values[article_id])
            articles_df["title_translated"].values[article_id] = re.sub(r"\b%s\b"%word, word.lower(), articles_df["title_translated"].values[article_id])
            articles_df["keywords_translated"].values[article_id] = re.sub(r"\b%s\b"%word, word.lower(), articles_df["keywords_translated"].values[article_id])
    return articles_df

def get_similar_word_by_symbol_replacement(word, symbol, symbol_to_replace, search_engine_inverted_index):
    if symbol in word and len(word) > 5 and " " not in word:
        text = word
        while text != "":
            try:
                ind = text.rindex(symbol)
                if ind < len(word) - 1 and ind > 1:
                    new_word = word[:ind] + symbol_to_replace + word[ind+1:]
                    if len(search_engine_inverted_index.get_articles_by_word(new_word)) > 0:
                        return new_word
                text = text[:ind]
            except:
                text = ""
    return ""

def replaced_with_z_s_symbols_words(word, search_engine_inverted_index):
    new_words = set()
    new_word = get_similar_word_by_symbol_replacement(word, "s","z",search_engine_inverted_index)
    if new_word.strip() != "":
        new_words.add(new_word)
    new_word = get_similar_word_by_symbol_replacement(word, "z","s",search_engine_inverted_index)
    if new_word.strip() != "":
        new_words.add(new_word)
    return new_words

def clean_text_from_commas(word, marks = ",.;?!"):
    ind = 0
    while ind < len(word):
        if word[ind] in marks or word[ind:ind+1].strip() == "":
            ind +=1
        else:
            break
    word = word[ind:]
    ind = len(word) -1
    last_sym = ""
    while ind >= 0:
        if word[ind] in marks or word[ind:ind+1].strip() == "":
            ind -=1
            if word[ind] in ".?!":
                last_sym = word[ind]
        else:
            break
    word = word[:ind+1] + last_sym
    return word