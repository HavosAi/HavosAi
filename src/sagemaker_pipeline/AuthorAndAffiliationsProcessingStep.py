
import json
import pandas as pd
import os
from src.text_processing.author_and_affiliations_processing import AuthorAndAffiliationsProcessing
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, OUTPUTS_DIR

  
if __name__ == "__main__":
    print("/opt/ml/processing/data", os.listdir("/opt/ml/processing/data"))
    # tmp
    df_ex = pd.read_excel("/opt/ml/processing/data/districts.xlsx")
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
        f"{INPUTS_DIR}/JournalNormalizerOutput.csv",
        sep=';',
        index_col=0,
    )

    if config["Steps"]["AuthorAndAffiliationsProcessingStep"]["Apply"] == "True":
        print("AuthorAndAffiliationsProcessingStep", "true")
        os.chdir("/opt/ml/processing/data")
        df_ex = pd.read_excel("../data/GeoRegions.xlsx")
        df = AuthorAndAffiliationsProcessing().process_authors_and_affiliations(df)
        os.chdir("/")
    else:
        print("AuthorAndAffiliationsProcessingStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/AuthorAndAffiliationsProcessingOutput.csv", sep=';')
