
import json
import pandas as pd
import os
import pickle
from src.text_processing.column_filler import ColumnFiller
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, SEARCH_INPUTS_DIR, ABBREV_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    df_tmp = pd.read_excel("/opt/ml/processing/data/population_tags.xlsx")
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/PopulationTagsFinderOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{SEARCH_INPUTS_DIR}/search_index.pickle", "rb") as outfile:
        search_index = pickle.load(outfile)
    with open(f"{ABBREV_INPUTS_DIR}/abbreviation_resolver.pickle", "rb") as outfile:
        abbreviation_resolver = pickle.load(outfile)
    
    print("Abbreviation_resolver check:")
    print(type(abbreviation_resolver))
    try:
        print(type(abbreviation_resolver.abbreviations_finder_dict))
    except:
        print("error: abbreviations_finder_dict")  
    try:
        print(type(abbreviation_resolver.resolved_abbreviations))
    except:
        print("error: resolved_abbreviations") 
    try:
        print(type(abbreviation_resolver.words_to_abbreviations))
    except:
        print("error: words_to_abbreviations")
    try:
        print(type(abbreviation_resolver.sorted_resolved_abbreviations))
    except:
        print("error: sorted_resolved_abbreviations")
    try:
        print(type(abbreviation_resolver.sorted_words_to_abbreviations))
    except:
        print("error: sorted_words_to_abbreviations")
    
    if config["Steps"]["ColumnFillerStep"]["Apply"] == "True":
        print("ColumnFillerStep", "true")
        os.chdir("/opt/ml/processing/data")
        df = ColumnFiller(
            dict_filename="../data/population_tags.xlsx",
        ).label_articles_with_outcomes(
            "gender_age_population_tags", 
            df, 
            search_index, 
            abbreviation_resolver,
        )
        os.chdir("/")
    else:
        print("ColumnFillerStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/ColumnFillerOutput.csv", sep=';')
