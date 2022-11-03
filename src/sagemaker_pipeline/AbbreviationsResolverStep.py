
import json
import pandas as pd
import pickle
from src.text_processing.abbreviations_resolver import AbbreviationsResolver
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
        f"{INPUTS_DIR}/subfolder-0-reduced.csv",
        sep=';',
        index_col=0,
    )
    df.to_csv(f"{OUTPUTS_DIR}/AbbreviationsResolverOutput.csv", sep=';')
    
    
    if config["Steps"]["AbbreviationsResolverStep"]["Apply"] == "True":
        print("AbbreviationsResolverStep", "true")
        
        abbreviations_resolver = AbbreviationsResolver([]) 
        abbreviations_resolver.load_model(f"{MODELS_INPUTS_DIR}")
        
        print("Test before dump:")
        print(type(abbreviations_resolver.abbreviations_finder_dict), 
              type(abbreviations_resolver.sorted_resolved_abbreviations))
        
        with open(f"{OUTCOMES_MODEL}/abbreviation_resolver.pickle", "wb") as outfile:
            pickle.dump(abbreviations_resolver, outfile)
            
        print("Test after dump:")
        with open(f"{OUTCOMES_MODEL}/abbreviation_resolver.pickle", "rb") as outfile:
            abbreviations_resolver2 = pickle.load(outfile)
        print(type(abbreviations_resolver2.abbreviations_finder_dict), 
              type(abbreviations_resolver2.sorted_resolved_abbreviations))
        
    else:
        print("AbbreviationsResolverStep", "false")
