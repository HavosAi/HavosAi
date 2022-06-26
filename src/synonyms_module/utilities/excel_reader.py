import pandas as pd
import os

class ExcelReader:

    def __init__(self):
        pass

    def read_file(self, filename):
        df = pd.DataFrame()
        if filename.split(".")[-1] == "csv":
            try:
                df = pd.read_csv(filename).fillna("")
            except:
                df = pd.read_csv(filename, encoding='ISO-8859-1').fillna("")
        if filename.split(".")[-1] == "xlsx":
            df = pd.read_excel(filename).fillna("")
        if len(df) == 0:
            print("filename %s has incorrect extension or it is an empty file"%filename)
        assert len(df) != 0
        return df

    def read_df_from_excel(self, filename):
        articles_df_saved = self.read_file(filename)
        for i in range(len(articles_df_saved)):
            for column in articles_df_saved.columns:
                try:
                    if type(eval(articles_df_saved[column].values[i])) == list:
                        articles_df_saved[column].values[i] = eval(articles_df_saved[column].values[i])
                except:
                    pass
        return articles_df_saved

    def read_distributed_df_from_excel(self, folder):
        files_count = len(os.listdir(folder))
        full_df = pd.DataFrame()
        for filename_id in range(files_count):
            temp_df = self.read_df_from_excel(os.path.join(folder, "%d.xlsx"%filename_id))
            full_df = pd.concat([full_df, temp_df], sort=False)
        return full_df

    def read_distributed_df_sequantially(self, folder):
        files_count = len(os.listdir(folder))
        for filename_id in range(files_count):
            yield self.read_df_from_excel(os.path.join(folder, "%d.xlsx"%filename_id))
