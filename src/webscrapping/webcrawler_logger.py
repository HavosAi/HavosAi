import uuid
import os
import pickle

class WebcrawlerLogger:

    def __init__(self, log_status_filename):
        self.log_status_filename = log_status_filename
        self.initialize_from_file()

    def initialize_log_info(self, urls):
        urls_order = []
        urls_info = {}
        for url in urls:
            url = url.strip()
            if url != "" and url not in urls_info:
                url_unique_id = uuid.uuid4().hex
                urls_info[url] = {"unique_id": url_unique_id, "total_articles_count": 0, "processed_articles_count": 0, "errors":[], "status":"Pending"}
                urls_order.append(url)
        self.info = {"urls_info": urls_info, "urls_order": urls_order,"status":"In Progress", "is_ready_to_download":False}
        self.save_info()

    def save_info(self):
        if self.log_status_filename.strip() != "":
            with open(self.log_status_filename, "wb") as f:
                pickle.dump(self.info, f)

    def initialize_from_file(self):
        if os.path.exists(self.log_status_filename):
            with open(self.log_status_filename, "rb") as f:
                self.info = pickle.load(f)
        else:
            self.info = {"urls_info": {}, "urls_order": [], "status":"In Progress", "is_ready_to_download":False}

    def update_status(self, status):
        self.initialize_from_file()
        self.info["status"] = status
        self.save_info()

    def perform_final_checks_for_query(self, query):
        self.initialize_from_file()
        if query in self.info["urls_info"]:
            if self.info["urls_info"][query]["processed_articles_count"] != self.info["urls_info"][query]["total_articles_count"]:
                self.info["urls_info"][query]["errors"].append("This query had %d duplicates"%abs( self.info["urls_info"][query]["total_articles_count"] - self.info["urls_info"][query]["processed_articles_count"]))
        self.save_info()

    def update_status_for_query(self, query, status, errors = ""):
        self.initialize_from_file()
        if query in self.info["urls_info"]:
            errors = errors.strip()
            if errors != "" and errors not in self.info["urls_info"][query]["errors"]:
                self.info["urls_info"][query]["errors"].append(errors)
            if self.info["urls_info"][query]["status"]  != "Finished with errors":
                self.info["urls_info"][query]["status"] = status
        self.save_info()

    def update_webscrapping_results(self, query, processed_links, articles_in_page, errors = ""):
        self.initialize_from_file()
        if query in self.info["urls_info"]:
            errors = errors.strip()
            self.info["urls_info"][query]["processed_articles_count"] += len(processed_links)
            self.info["urls_info"][query]["total_articles_count"] += articles_in_page
            if errors != "" and errors not in self.info["urls_info"][query]["errors"]:
                self.info["urls_info"][query]["errors"].append(errors)
        self.save_info()

    def perform_final_checks(self, is_ready_to_download = False):
        self.initialize_from_file()
        all_finished = True
        without_errors = True
        for query in self.info["urls_info"]:
            if not self.info["urls_info"][query]["status"] == "Finished" and not self.info["urls_info"][query]["status"] == "Finished with errors":
                all_finished = False
                break
            if self.info["urls_info"][query]["status"] == "Finished with errors":
                without_errors = False
        self.info["status"] = ("Finished" if without_errors else "Finished with errors") if all_finished else "In Progress"
        self.info["is_ready_to_download"] = is_ready_to_download
        self.save_info()

    def update_status_for_cancelling(self):
        self.initialize_from_file()
        self.info["status"] = "Cancelled" if self.info["status"] == "In Progress" else self.info["status"]
        for query in self.info["urls_info"]:
            self.info["urls_info"][query]["status"] = "Pending" if self.info["urls_info"][query]["status"] == "In Progress" else self.info["urls_info"][query]["status"]
        self.save_info()






