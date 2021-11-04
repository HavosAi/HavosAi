import sys
sys.path.append('../src')

from text_processing import text_normalizer, context_extender, extended_context_splitter
from utilities import excel_writer, excel_reader
import argparse
import pandas as pd
import pickle
import os
from interventions_labeling_lib import hyponym_statistics
from time import time
import nltk
import re

def write_buf_in_file_df(rows_to_write, columns, start_pos, folder):
    os.makedirs(folder, exist_ok=True)
    file_to_write = "{}/docs_with_sentences_from_{}_to{}.xlsx".format(folder, start_pos, start_pos+len(rows_to_write))
    if os.path.exists(file_to_write):
        print("WARNING rewrite file ", file_to_write)
    excel_writer.ExcelWriter().save_data_in_excel(rows_to_write, columns, file_to_write)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_to_read', default = "")
    parser.add_argument('--column_to_use', default = "")
    parser.add_argument('--intervention_type', default = "standard")
    parser.add_argument('--columns_for_uniqueness', default = "country_project_id,intervention,context,real_sentence")
    parser.add_argument('--simple_cache_context_folder', default = "../tmp/ifad_documents/cache_data/context")
    parser.add_argument('--folder_to_write_contexts', default = "")
    parser.add_argument('--folder_to_write_split_contexts', default = "")
    parser.add_argument('--folder_to_write_result', default = "")
    parser.add_argument('--folder_to_write_cleaned', default = "")
    parser.add_argument('--file_with_intervention_translations', default = "")
    parser.add_argument('--all_steps', dest='all_steps', action='store_true')
    parser.set_defaults(all_steps=False)
    parser.add_argument('--only_contexts', dest='only_contexts', action='store_true')
    parser.set_defaults(only_contexts=False)
    parser.add_argument('--only_contexts_split', dest='only_contexts_split', action='store_true')
    parser.set_defaults(only_contexts_split=False)
    parser.add_argument('--only_contexts_split_result_merge', dest='only_contexts_split_result_merge', action='store_true')
    parser.set_defaults(only_contexts_split_result_merge=False)
    parser.add_argument('--only_contexts_clean', dest='only_contexts_clean', action='store_true')
    parser.set_defaults(only_contexts_clean=False)

    args = parser.parse_args()

    print("File to read: %s"%args.file_to_read)
    print("Column to use: %s"%args.column_to_use)
    print("Column for uniqueness: %s"%args.columns_for_uniqueness)
    print("File with intervention translations: %s"%args.file_with_intervention_translations)
    print("Invervention type: %s"%args.intervention_type)
    print("Folder to write extended contexts: %s"%args.folder_to_write_contexts)
    print("Folder to write split contexts: %s"%args.folder_to_write_split_contexts)
    print("Folder to write a resulted dataset: %s"%args.folder_to_write_result)
    print("Folder to write a cleaned dataset: %s"%args.folder_to_write_cleaned)
    print("Folder to the context cache: %s"%args.simple_cache_context_folder)
    print("All steps to perform: %s"%args.all_steps)
    print("Only contexts: %s"%args.only_contexts)
    print("Only contexts split: %s"%args.only_contexts_split)
    print("Only contexts split: %s"%args.only_contexts_split_result_merge)
    print("Only context clean: %s"%args.only_contexts_clean)

    args.columns_for_uniqueness = [column.strip() for column in args.columns_for_uniqueness.split(",")]

    df = excel_reader.ExcelReader().read_df_from_excel(args.file_to_read)

    intervation_translation_map = {}
    if os.path.exists(args.file_with_intervention_translations):
        df_translated_interventions = excel_reader.ExcelReader().read_df_from_excel(args.file_with_intervention_translations)
        for i in range(len(df_translated_interventions)):
            foreign = df_translated_interventions["foreign word"].values[i].strip()
            english = df_translated_interventions["english word"].values[i].strip()
            intervation_translation_map[foreign] = english
        print(f"Total dictionary length {len(intervation_translation_map)}")

    if args.all_steps or args.only_contexts:
        simple_cache_context = context_extender.SimpleCacheContext(args.simple_cache_context_folder)
        rows_to_write = []
        already_writed = 0

        for i in range(len(df)):
            used_contexts = set()
            country_name = df["Country"].values[i].lower().strip()
            project_id = str(df["ID"].values[i]).lower().strip()
            report_type = df["Type of report"].values[i].strip()
            report_composition_id = (country_name, project_id, report_type)

            all_interventions = [text_normalizer.normalize_sentence(item) for item in df[args.column_to_use].values[i]]

            print(report_composition_id, i)
            print(all_interventions)
            print(f"Should process #{len(all_interventions)} intervention on page")
            cur_text = df["abstract"].values[i]
            cur_extender_generator = context_extender.IntervectionContextsFromPageExtractor(
                cur_text, list(all_interventions), intervation_translation_map, my_map_cache=simple_cache_context).extender_generator()
            reverse_ind = i
            for intervention_in_english, context, cur_text_sentence, several_sentences in cur_extender_generator:
                if context in used_contexts:
                    continue
                if intervention_in_english == context:
                    continue
                used_contexts.add(context)
                rows_to_write.append(list(df.values[reverse_ind]) + [intervention_in_english, cur_text_sentence,
                                                                     context, several_sentences, args.intervention_type])
                
            
            simple_cache_context.print_statistics()
            if len(rows_to_write) > 1000:
                print("Write buf in file")
                write_buf_in_file_df(rows_to_write, list(df.columns) + ['intervention', 'real_sentence', 'context', 'several_sentences', 'intervention_type'],
                    already_writed, args.folder_to_write_contexts)
                already_writed += len(rows_to_write)
                rows_to_write = []
                simple_cache_context.save_additional_data()
                
        if len(rows_to_write) > 0:
            print("Write buf in file")
            write_buf_in_file_df(rows_to_write, list(df.columns) + ['intervention', 'real_sentence', 'context', 'several_sentences', 'intervention_type'],
                    already_writed, args.folder_to_write_contexts)
            already_writed += len(rows_to_write)
            rows_to_write = []
            simple_cache_context.save_additional_data()

    if args.all_steps or args.only_contexts_split:
        os.makedirs(args.folder_to_write_split_contexts, exist_ok=True)
        _extended_context_splitter = extended_context_splitter.ExtendedContextSplitter()

        for file in os.listdir(args.folder_to_write_contexts):
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(args.folder_to_write_contexts, file))
            all_contexts = []

            all_contexts = []
            cnt = 0
            for i in range(len(df)):
                if i % 1000 == 0:
                    print("%d processed" % i)
                full_context_rows = _extended_context_splitter.split_extended_contexts(
                    df["real_sentence"].values[i], df["intervention"].values[i],
                    df["context"].values[i], df["intervention_type"].values[i])

                if not full_context_rows:
                    print(i)
                    print(df["intervention_type"].values[i])
                    print(df["intervention"].values[i])
                    print(df["context"].values[i])
                    print(df["real_sentence"].values[i])
                all_contexts.append(full_context_rows)
            file_save = os.path.basename(file) + ".pickle"
            pickle.dump(all_contexts, open(os.path.join(args.folder_to_write_split_contexts, file_save), "wb"))

    if args.all_steps or args.only_contexts_split_result_merge:
        os.makedirs(args.folder_to_write_result, exist_ok=True)

        for file in os.listdir(args.folder_to_write_split_contexts):
            initial_file = file.split(".pickle")[0]
            df = excel_reader.ExcelReader().read_df_from_excel(os.path.join(args.folder_to_write_contexts, initial_file))
            all_found_contexts = pickle.load(open(os.path.join(args.folder_to_write_split_contexts, file), "rb"))
            df_values = df.values
            new_rows = []
            ind_context_column = list(df.columns).index("context")
            ind_intervention_column = list(df.columns).index("intervention")

            for i in range(len(df)):
                if len(all_found_contexts[i]) == 0 and df["intervention_type"].values[i] == "standard":
                    new_rows.append(list(df_values[i]))
                if len(all_found_contexts[i]) == 0 and df["intervention_type"].values[i] != "standard":
                    continue
                if len(all_found_contexts[i]) >= 1:
                    for interv, context in all_found_contexts[i]:
                        new_data_point = list(df_values[i])
                        new_data_point[ind_context_column] = context
                        new_data_point[ind_intervention_column] = interv
                        new_rows.append(new_data_point)
            excel_writer.ExcelWriter().save_data_in_excel(new_rows, list(df.columns), os.path.join(args.folder_to_write_result, initial_file))

    if args.all_steps or args.only_contexts_clean:
        all_df = pd.DataFrame()
        _hyp_stat = hyponym_statistics.HyponymStatistics({}, {}, {}, {}, {})
        _extend_context_splitter = extended_context_splitter.ExtendedContextSplitter()

        for file in os.listdir(args.folder_to_write_result):
            df_new = excel_reader.ExcelReader().read_df_from_excel(os.path.join(args.folder_to_write_result, initial_file))

            ind_to_take = []
            cnt = 0
            for i in range(len(df_new)):
                if _hyp_stat.clean_concept(df_new["context"].values[i]) != df_new["context"].values[i]:
                    cleaned_interv = _extend_context_splitter.clean_from_filter_words(
                        _hyp_stat.clean_concept(df_new["context"].values[i]), _extend_context_splitter.stopwords_crops_normalized)
                    if not cleaned_interv.strip() and df_new["intervention"].values[i] in ["start ups"]:
                        df_new["context"].values[i] = df_new["intervention"].values[i]
                    if df_new["context"].values[i] == df_new["intervention"].values[i]:
                        df_new["intervention"].values[i] = cleaned_interv
                    df_new["context"].values[i] = cleaned_interv
                    cnt += 1
                if len(df_new["context"].values[i].strip()) > 100:
                    df_new["context"].values[i] = df_new["intervention"].values[i]
                for column in ["intervention", "context", "real_sentence"]:
                    df_new[column].values[i] = df_new[column].values[i].strip()
                if df_new["context"].values[i].strip():
                    ind_to_take.append(i)
            print(file, " Number of changed ", cnt)
            all_df = pd.concat([all_df, df_new.take(ind_to_take)], axis=0)


        unique_rows = []
        unique_keys = set()
        for i in range(len(all_df)):
            country_project_id = tuple(
                [all_df[column].values[i] if type(all_df[column].values[i]) is not str else all_df[column].values[i].strip()\
                    for column in args.columns_for_uniqueness])
            if country_project_id not in unique_keys:
                unique_keys.add(country_project_id)
                unique_rows.append(i)
        print("All rows ", len(all_df))
        print("Unique rows ", len(unique_rows))

        all_df = all_df.take(unique_rows)
        excel_writer.ExcelWriter().save_big_data_df_in_excel(all_df, args.folder_to_write_cleaned)



