import webscrapping
from webscrapping import webcrawler_agris
from webscrapping import webcrawler_ifpri
from webscrapping import webcrawler_world_bank
from webscrapping import webcrawler_world_bank_ieg
from webscrapping import webcrawler_iadb
from webscrapping import webcrawler_eldis
from webscrapping import webcrawler_care_eval
from webscrapping import webcrawler_cgdev
from webscrapping import webcrawler_google_scholar
from webscrapping import webcrawler_usaid_ll
from webscrapping import webcrawler_gef
from webscrapping import webcrawler_gardian_json
from webscrapping import webcrawler_cee
from webscrapping import webcrawler_cast
from webscrapping import webcrawler_ipa
from webscrapping import webcrawler_odi
from webscrapping import webcrawler_dfid
from webscrapping import webcrawler_ifad
from webscrapping import webcrawler_iied
from webscrapping import webcrawler_csiro
from webscrapping import webcrawler_cirad
from webscrapping import webcrawler_agecon
from webscrapping import webcrawler_embrapa
from webscrapping import webcrawler_who
from webscrapping import webcrawler_unep
from webscrapping import webcrawler_wfp
from webscrapping import webcrawler_datad
from webscrapping import webcrawler_campbell
from webscrapping import webcrawler_cirad_fr
from webscrapping import webcrawler_logger
from webscrapping import webcrawler_usaid
from webscrapping import webcrawler_repo_mel_cgiar
from webscrapping import webcrawler_cgspace
from webscrapping import webcrawler_dfid_devtracker
from webscrapping import webcrawler_irc
from webscrapping import webcrawler_rwsn
from webscrapping import webcrawler_sanitationall
import pandas as pd
import os
from utilities import excel_writer
import uuid
import pickle
from utilities import excel_reader
import sys
import traceback

class WebcrawlerMain:

    def __init__(self, unique_id = "", log_status_filename = ""):
        self.sources_dict = {
        "http://agris.fao.org": webscrapping.webcrawler_agris.WebCrawlerAGRIS(),
        "http://ebrary.ifpri.org": webscrapping.webcrawler_ifpri.WebCrawlerIFPRI(),
        "http://openknowledge.worldbank.org": webscrapping.webcrawler_world_bank.WebCrawlerWorldBank(),
        "http://ieg.worldbankgroup.org": webscrapping.webcrawler_world_bank_ieg.WebCrawlerWorldBankIEG(), #new REAPER_1
        "http://publications.iadb.org": webscrapping.webcrawler_iadb.WebCrawlerIADB(), #new REAPER_2
        "http://www.eldis.org/": webscrapping.webcrawler_eldis.WebCrawlerEldis(), #new REAPER_3
        "http://careevaluations.org": webscrapping.webcrawler_care_eval.WebCrawlerCareEval(), #new REAPER_4
        "https://www.cgdev.org": webscrapping.webcrawler_cgdev.WebCrawlerCGDev(), #new REAPER_5
        "https://scholar.google.com": webscrapping.webcrawler_google_scholar.WebCrawlerGoogleScholar(), #new REAPER_6
        "https://usaidlearninglab.org": webscrapping.webcrawler_usaid_ll.WebCrawlerUSAIDLearnLab(), #new REAPER_9
        "https://www.gefieo.org": webscrapping.webcrawler_gef.WebCrawlerGEF(), #new REAPER_10
        "http://gardian.bigdata.cgiar.org": webscrapping.webcrawler_gardian_json.WebCrawlerGARDIAN_JSON(),
        "http://www.environmentalevidence.org": webscrapping.webcrawler_cee.WebCrawlerCEE(),
        "http://www.cast-science.org": webscrapping.webcrawler_cast.WebCrawlerCAST(),
        "http://www.poverty-action.org": webscrapping.webcrawler_ipa.WebCrawlerIPA(),
        "http://www.odi.org": webscrapping.webcrawler_odi.WebCrawlerODI(),
        "http://www.gov.uk": webscrapping.webcrawler_dfid.WebCrawlerDFID(),
        "http://www.ifad.org": webscrapping.webcrawler_ifad.WebCrawlerIFAD(),
        "http://pubs.iied.org": webscrapping.webcrawler_iied.WebCrawlerIIED(),
        "http://publications.csiro.au": webscrapping.webcrawler_csiro.WebCrawlerCSIRO(),
        "http://agritrop.cirad.fr": webscrapping.webcrawler_cirad.WebCrawlerCIRAD(),
        "http://ageconsearch.umn.edu": webscrapping.webcrawler_agecon.WebCrawlerAGECON(),
        "http://www.embrapa.br": webscrapping.webcrawler_embrapa.WebCrawlerEMBRAPA(),
        "http://apps.who.int": webscrapping.webcrawler_who.WebCrawlerWHO(),
        "http://wedocs.unep.org": webscrapping.webcrawler_unep.WebCrawlerUNEP(),
        "http://www1.wfp.org": webscrapping.webcrawler_wfp.WebCrawlerWFP(),
        "http://datad.aau.org": webscrapping.webcrawler_datad.WebCrawlerDATAD(),
        "http://www.campbellcollaboration.org": webscrapping.webcrawler_campbell.WebCrawlerCampbell(),
        "http://www.cirad.fr": webscrapping.webcrawler_cirad_fr.WebCrawlerCIRAD_fr(),
        "http://dec.usaid.gov": webscrapping.webcrawler_usaid.WebCrawlerUsaid(),
        "http://repo.mel.cgiar.org": webcrawler_repo_mel_cgiar.WebCrawlerRepoMelCGIAR(),
        "http://cgspace.cgiar.org": webcrawler_cgspace.WebCrawlerCGSPACE(),
        "http://devtracker.dfid.gov.uk": webcrawler_dfid_devtracker.WebCrawlerDFIDDevtracker(),
        "http://www.ircwash.org": webcrawler_irc.WebCrawlerIRC(),
        "http://www.rural-water-supply.net": webcrawler_rwsn.WebCrawlerRWSN(),
        "http://www.sanitationandwaterforall.org": webcrawler_sanitationall.WebCrawlerSanitationAll()
        }
        self.unique_id = uuid.uuid4().hex if unique_id == "" else unique_id
        self.log_status_filename = log_status_filename
        self.webcrawler_logger = webcrawler_logger.WebcrawlerLogger(self.log_status_filename)

    def crawl_and_prepare_dataset_by_query(self, query, folder_to_save, dataset_filename):
        domain = "/".join(query.split("/")[:3]).replace("https:", "http:")
        if domain in self.sources_dict:
            try:
                print("Started querying for source: %s" %domain)
                self.webcrawler_logger.update_status_for_query(query, "In Progress")
                self.sources_dict[domain].crawl_query(query, folder_to_save, log_status_filename = self.log_status_filename)
                self.webcrawler_logger.perform_final_checks_for_query(query)
                self.sources_dict[domain].prepare_dataset(folder_to_save, dataset_filename)
                self.webcrawler_logger.update_status_for_query(query, "Finished")
            except:
                traceback.print_exc()
                print("Couldn't websrap for source: %s"%domain)
                self.webcrawler_logger.update_status_for_query(query, "Finished with errors", errors = "Finished with errors")
        else:
            print("Unknown source domain: %s"%domain)
            self.webcrawler_logger.update_status_for_query(query, "Finished with errors", errors = "Unknown source domain")

    def crawl_all_sources_from_file(self, folder_name):
        for url in self.webcrawler_logger.info["urls_order"]:
            url_unique_id = self.webcrawler_logger.info["urls_info"][url]["unique_id"]
            url_folder_name =  os.path.join(folder_name, url_unique_id)
            self.crawl_and_prepare_dataset_by_query(url, url_folder_name, os.path.join(folder_name, url_unique_id + ".xlsx"))
        self.save_dataset_from_all_sources(folder_name)


    def save_dataset_from_all_sources(self, folder):
        df = pd.DataFrame()
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if (".xlsx" in file) and (file != os.path.basename(folder) + ".xlsx"):
                    new_dataset = excel_reader.ExcelReader().read_df_from_excel(os.path.join(folder, file))
                    df= pd.concat([df, new_dataset], sort=False)
            if len(df) > 0:
                excel_writer.ExcelWriter().save_df_in_excel(df,os.path.join(folder,os.path.basename(folder)  + ".xlsx"))
        self.webcrawler_logger.perform_final_checks(is_ready_to_download = (len(df) > 0))
