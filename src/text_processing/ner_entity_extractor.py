import spacy
import nltk

class NEREntityExtractor:

    def __init__(self, model_folder):
        self.model = spacy.load(model_folder)

    def find_ner_entities(self, articles_df, columns_to_process=["abstract"], column_name="column_with_ner", entity_labels=[]):
        articles_df[column_name] = ""
        for i in range(len(articles_df)):
            result_set = set()
            for column in columns_to_process:
                for sentence in nltk.sent_tokenize(articles_df[column].values[i]):
                    for r in self.model(sentence).ents:
                        if not entity_labels or r.label_ in entity_labels:
                            result_set.add(r.text.strip())
            articles_df[column_name].values[i] = list(result_set)
            if i % 3000 == 0:
                print("Processed %d rows" % i)
        return articles_df