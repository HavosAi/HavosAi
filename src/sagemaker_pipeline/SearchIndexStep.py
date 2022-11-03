
import json
import pandas as pd
import pickle
from src.text_processing.search_engine_insensitive_to_spelling import SearchEngineInsensitiveToSpelling
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
        f"{INPUTS_DIR}/AbbreviationsResolverOutput.csv",
        sep=';',
        index_col=0,
    )
    df.to_csv(f"{OUTPUTS_DIR}/SearchIndexOutput.csv", sep=';')
    
    
    if config["Steps"]["SearchIndexStep"]["Apply"] == "True":
        print("SearchIndexStep", "true")
        search_engine = SearchEngineInsensitiveToSpelling(
            abbreviation_folder=MODELS_INPUTS_DIR, 
            load_abbreviations=True,
        )
        search_engine.create_inverted_index(df)
        with open(f"{OUTCOMES_MODEL}/search_index.pickle", "wb") as outfile:
            pickle.dump(search_engine, outfile)
    else:
        print("SearchIndexStep", "false")
