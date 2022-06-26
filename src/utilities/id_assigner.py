import os
import pandas as pd

class IdAssigner:

	def __init__(self, global_id_source = "../model/glob_lastId.txt"):
		self.global_id_source = global_id_source
		self.initialize_last_id(self.global_id_source)

	def initialize_last_id(self, filepath):
		if os.path.exists(filepath):
			with open(filepath, "r") as f:
				try:
					self.last_id = int(f.read())
				except:
					self.last_id = -1

	def save_last_id(self):
		with open(self.global_id_source, "w") as f:
			f.write(str(self.last_id))

	def fill_id_in_df(self, df, id_column = "id"):
		if id_column not in df:
			df[id_column] = ""
		for i in range(len(df)):
			try:
				_id = int(df[id_column].values[i])
				df[id_column].values[i] = _id
			except:
				self.last_id += 1
				df[id_column].values[i] = int(self.last_id)
		df[id_column] = pd.to_numeric(df[id_column], downcast='integer')
		self.save_last_id()
		return df