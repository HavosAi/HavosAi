
import json
import pandas as pd
import os
import pickle
from src.text_processing.geo_names_finder import GeoNameFinder
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    print("/opt/ml/processing/data", os.listdir("/opt/ml/processing/data"))
    # tmp
    df_ex = pd.read_excel("/opt/ml/processing/data/districts.xlsx")
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/AuthorAndAffiliationsProcessingOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{MODELS_INPUTS_DIR}/search_index.pickle", "rb") as outfile:
        search_index = pickle.load(outfile)
    if config["Steps"]["GeoNameFinderStep"]["Apply"] == "True":
        print("GeoNameFinderStep", "true")
        os.chdir("/opt/ml/processing/data")
        df = GeoNameFinder().label_articles_with_geo_names(df, search_index)
        os.chdir("/")
    else:
        print("GeoNameFinderStep", "false")
    print(f"saving to {OUTPUTS_DIR}/GeoNameFinderOutput.csv")
    df.to_csv(f"{OUTPUTS_DIR}/GeoNameFinderOutput.csv", sep=';')
    print("saved")
