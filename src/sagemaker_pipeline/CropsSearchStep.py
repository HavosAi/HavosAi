
import json
import pandas as pd
import os
import pickle
from src.text_processing.crops_finder import CropsSearch
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    print("/opt/ml/processing/data", os.listdir("/opt/ml/processing/data"))
    # tmp
    df_ex = pd.read_excel("/opt/ml/processing/data/districts.xlsx")
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/GeoNameFinderOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{MODELS_INPUTS_DIR}/search_index.pickle", "rb") as outfile:
        search_index = pickle.load(outfile)
    if config["Steps"]["CropsSearchStep"]["Apply"] == "True":
        print("CropsSearchStep", "true")
        os.chdir("/opt/ml/processing/data")
        df = CropsSearch(
            search_index, 
            "../data/map_plant_products.xlsx"
        ).find_crops(df, column_name="plant_products_search")
        df = CropsSearch(
            search_index, 
            "../data/map_animal_products.xlsx"
        ).find_crops(df, column_name="animal_products_search")
        df = CropsSearch(
            search_index, 
            "../data/map_animals.xlsx"
        ).find_crops(df, column_name="animals_found")
        os.chdir("/")
    else:
        print("CropsSearchStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/CropsSearchOutput.csv", sep=';')
