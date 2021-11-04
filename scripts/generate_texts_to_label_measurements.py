import sys
sys.path.append('../src')
import argparse
from utilities import excel_reader
from utilities import excel_writer
from text_processing import text_normalizer
import nltk
from time import time
import re
from sklearn.utils import shuffle
import spacy

def check_train_test_collisions(train, test):
    sentence_set = set()
    for i in range(len(train)):
        num_res = train["Number"].values[i] if type(train["Number"].values[i]) != str else train["Number"].values[i].strip()
        sentence_set.add((re.sub("\s+", " ", train["Sentence"].values[i].lower()).strip(), 
                         num_res, re.sub("\s+", " ", train["Word Expression"].values[i].lower()).strip()))
    only_sentence_set = set()
    for i in range(len(train)):
        only_sentence_set.add(re.sub("\s+", " ", train["Sentence"].values[i].lower()).strip())
    print("Train data sentences:", len(sentence_set))
    print("Train data only sentences: ", len(only_sentence_set))
    cnt = 0
    cnt_sent = 0
    for i in range(len(test)):
        num_res = test["Number"].values[i] if type(test["Number"].values[i]) != str else test["Number"].values[i].strip()
        result = (re.sub("\s+", " ", test["Sentence"].values[i].lower()).strip(), 
                         num_res, re.sub("\s+", " ", test["Word Expression"].values[i].lower()).strip())
        if result in sentence_set:
            print(result)
            cnt += 1
        if re.sub("\s+", " ", test["Sentence"].values[i].lower()).strip() in only_sentence_set:
            cnt_sent += 1
    print("Coincided labelled data: ", cnt)
    print("Coincided sentences: ", cnt_sent)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count_to_take', default=50)
    parser.add_argument('--train_data_file', default="../tmp/measurements_data/train.xlsx")
    parser.add_argument('--test_data_file', default="../tmp/measurements_data/test.xlsx")

    nlp = spacy.load('en_core_web_sm')

    args = parser.parse_args()
    print("Count to take ", args.count_to_take)
    print("Train data file ", args.train_data_file)
    print("Test data file ", args.test_data_file)

    train = excel_reader.ExcelReader().read_df(args.train_data_file)
    test = excel_reader.ExcelReader().read_df(args.test_data_file)
    check_train_test_collisions(train, test)

    articles_df = excel_reader.ExcelReader().read_df("../tmp/all_sentences_measurements.xlsx")

    train_pairs = []
    train_pairs_interv = []
    articles_df = shuffle(articles_df)
    taken = 0
    for i in range(len(articles_df)):
        if taken >= args.count_to_take:
            break
        if articles_df["Taken"].values[i]:
            continue
        sentence = articles_df["Sentence"].values[i]
        sent_pairs = set()
        sent_pairs_interv = set()
        doc = nlp(sentence)
        doc_ents = nlp(sentence).ents
        for word in doc:
            if word.tag_ in "CD" and re.search("\d+",word.text) != None:
                root = [token for token in doc if token.text == word.text][0]
                to_check = True
                for w in doc_ents:
                    try:
                        if re.search(r"\b%s\b"%root.text.replace("(","\(").replace(")","\)"), w.text) != None and w.label_ == "DATE":
                            to_check = False
                            res = text_normalizer.normalize_sentence(w.text)
                            #if len(res) > 1:
                            #    sent_pairs.add((sentence, word.text, res))
                            break
                    except:
                        pass
                if to_check:
                    #for w in nlp(sentence).noun_chunks:
                    #    res = text_normalizer.normalize_sentence(w.text)
                    #    
                    #    if len(res.split()) > 1:
                    #        sent_pairs.add((sentence, word.text, res))
                    for intervention in articles_df["interventions_found_raw"].values[i]:
                        interv_set = set([intervention])
                        for interv in interv_set:
                            if interv in sentence:
                                sent_pairs_interv.add((sentence, word.text, interv))
                    for intervention in articles_df["animal_products_search_details"].values[i]:
                        interv_set = set([intervention])
                        for interv in interv_set:
                            if interv in sentence:
                                sent_pairs_interv.add((sentence, word.text, interv))
                    for intervention in articles_df["plant_products_search_details"].values[i]:
                        interv_set = set([intervention])
                        for interv in interv_set:
                            if interv in sentence:
                                sent_pairs_interv.add((sentence, word.text, interv))
                    for intervention in articles_df["animals_found_details"].values[i]:
                        interv_set = set([intervention])
                        for interv in interv_set:
                            if interv in sentence:
                                sent_pairs_interv.add((sentence, word.text, interv))
        if sent_pairs or sent_pairs_interv:
            taken += 1
            articles_df["Taken"].values[i] = 1
        train_pairs.extend(list(sent_pairs))
        train_pairs_interv.extend(list(sent_pairs_interv))

    print("All taken measurements to label: ", len(train_pairs_interv))

    print("All taken: ", len(articles_df[articles_df["Taken"] == 1]))

    excel_writer.ExcelWriter().save_data_in_excel(train_pairs_interv, ["Sentence","Number","Word Expression"], "new_sample_%s.xlsx" %(int(time())))
    excel_writer.ExcelWriter().save_df_in_excel(articles_df, "../tmp/all_sentences_measurements.xlsx")