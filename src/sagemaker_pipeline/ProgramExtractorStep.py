
import json
import pandas as pd
import os
import pickle
from src.interventions_labeling_lib.programs_extractor import ProgramExtractor
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, SEARCH_INPUTS_DIR, ABBREV_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    df_tmp = pd.read_excel("/opt/ml/processing/data/extracted_programs.xlsx")
    with open(f"/opt/ml/processing/tmp/programs_extraction_model_2619/meta.json", "r") as file:
        json_tmp = json.load(file)
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/ColumnFillerOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{SEARCH_INPUTS_DIR}/search_index.pickle", "rb") as outfile:
        search_index = pickle.load(outfile)
    with open(f"{ABBREV_INPUTS_DIR}/abbreviation_resolver.pickle", "rb") as outfile:
        abbreviation_resolver = pickle.load(outfile)
    if config["Steps"]["ProgramExtractorStep"]["Apply"] == "True":
        print("ProgramExtractorStep", "true")
        os.chdir("/opt/ml/processing/data")
        df = ProgramExtractor([]).label_articles_with_programs(df, search_index, abbreviation_resolver)
        os.chdir("/")
    else:
        print("ProgramExtractorStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/ProgramExtractorOutput.csv", sep=';')
