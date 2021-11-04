import os
import shutil

class FolderCleaner:

	def __init__(self, folder, files_to_leave):
		self.folder = folder
		self.files_to_leave = files_to_leave

	def delete_files(self):
		for file in os.listdir(self.folder):
			if file not in self.files_to_leave:
				dir_to_delete = os.path.join(self.folder, file)
				if os.path.isdir(dir_to_delete):
					shutil.rmtree(dir_to_delete)
				else:
					os.remove(dir_to_delete)