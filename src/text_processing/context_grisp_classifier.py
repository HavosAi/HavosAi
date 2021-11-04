import sys
sys.path.append('../src')
import langdetect
from utilities import excel_writer, excel_reader
from text_processing import text_normalizer

import scipy
from collections import Counter
from synonyms_module import synonyms_processor

def simple_preprocessing(self, row):
    res = {}
    res['class'] = row['subcategory']
    res['context'] = row['context']
    res['nearest_item'] = row['nearest_item']
    return res

def get_simple_categorise_callback(word2vecModels, embeddings_with_subcategories, TOP_N=5):    
    def callback(preprocessed_pool_line):
        sent_for_search = preprocessed_pool_line["context"]
        embed_for_search = word2vecModels.get_average_embedding(sent_for_search)
        for_sort_list = []
        for key_item in embeddings_with_subcategories:
            debug_mode = 0
            key_item_embed = embeddings_with_subcategories[key_item]['embedding']
            dist_embeds = scipy.spatial.distance.cosine(embed_for_search, key_item_embed)
            if dist_embeds != dist_embeds:
                continue
            sent_subcategory = embeddings_with_subcategories[key_item]['subcategory']
            for_sort_list.append((dist_embeds, sent_subcategory, key_item))
        #print(for_sort_list)
        for_sort_list = sorted(for_sort_list, key=lambda x: x[0])
        if len(for_sort_list) < TOP_N:
            return (" ", " ", " ")
        subcategory_1 = for_sort_list[0][1]       
            
        c = Counter(for_sort_list[i][1] for i in range(TOP_N))
        subcategory_1 = c.most_common(1)[0][0]
        if c.most_common(1)[0][1] == 1:
            subcategory_1 = for_sort_list[0][1]
        return (subcategory_1, for_sort_list[0][2], for_sort_list[0][0])
    return callback

class GRIPSClassificationFiller:
    
    def __init__(self, status_logger = None,
            all_categories_file="../tmp/ifad_documents/GRIPS_simple_table.xlsx",
            distilled_categories_train="../tmp/ifad_documents/distilled_subcategory.xlsx",
            word_embeddings_folder="../model/synonyms_retrained_new",
            column_to_label="context",
            subcategory_column="subcategory",
            category_column="category"):
        self.status_logger = status_logger
        self.all_categories_file = all_categories_file
        self.distilled_categories_train = distilled_categories_train
        self.word_embeddings_folder = word_embeddings_folder
        self.column_to_label = column_to_label
        self.subcategory_column = subcategory_column
        self.category_column = category_column
        self.word2vecModels = synonyms_processor.SynonymsProcessor(word_embeddings_folder)

    def log_percents(self, percent):
        if self.status_logger is not None:
            self.status_logger.update_step_percent(percent)

    def label_with_grisp_categories(self, df):
        GRIPS_simple_table = excel_reader.ExcelReader().read_df_from_excel(self.all_categories_file)
        subcategory_to_category_map = {}
        for i in range(len(GRIPS_simple_table)):
            subcategory = GRIPS_simple_table["subcategory"].values[i]
            category = GRIPS_simple_table["category"].values[i]
            subcategory_to_category_map[subcategory] = (category + '/' + subcategory, category)

        classifier = ContextGrispClassifier(self.distilled_categories_train, self.word2vecModels)
        context_to_subcategory_map = {}
        df[self.category_column] = ""
        df[self.subcategory_column] = ""
        for i in range(len(df)):
            if i % 100 == 0:
                self.log_percents(i/len(df)*90)

            context = df[self.column_to_label].values[i].strip()
            predict_subcategory = ""
            if context in context_to_subcategory_map:
                predict_subcategory = context_to_subcategory_map[context]
            else:
                preprocessed_pool_line = {'context': context}
                predict_subcategory, nearest_item, nearest_dist = classifier.categorise(preprocessed_pool_line)
                context_to_subcategory_map[context] = predict_subcategory
            if predict_subcategory.strip() not in subcategory_to_category_map:
                predict_category, predict_subcategory = "", ""
            else:
                predict_category = subcategory_to_category_map[predict_subcategory][1]
                predict_subcategory = subcategory_to_category_map[predict_subcategory][0]
            df[self.category_column].values[i] = predict_category
            df[self.subcategory_column].values[i] = predict_subcategory
        return df

class ContextGrispClassifier:
    def __init__(self, file_path, word2vecModels, 
            callback_preprocessing_funk=simple_preprocessing):
        df_markuped = excel_reader.ExcelReader().read_df_from_excel(file_path)
        used_contexts = set()
        result = {}
        statistics = {}
        for i in range(len(df_markuped)):
            context = df_markuped["context"].values[i]
            subcategory = df_markuped["subcategory"].values[i]
            is_correct = df_markuped["is_correct"].values[i]
            if context in used_contexts:
                continue
            if is_correct < 1:
                continue
            if subcategory not in statistics:
                statistics[subcategory] = []
            statistics[subcategory].append(context) 
            used_contexts.add(context)
            result[context] = {}
            embedding = word2vecModels.get_average_embedding(context)
            result[context]['embedding'] = embedding
            result[context]['subcategory'] = subcategory
        self._embeddings_with_subcategories = result
        self._categorise_callback = get_simple_categorise_callback(
            word2vecModels, result, 5)
        self._statistics = statistics

    def categorise(self, preprocessed_pool_line):
        return self._categorise_callback(preprocessed_pool_line)

    def get_statistics(self):
        return self._statistics

