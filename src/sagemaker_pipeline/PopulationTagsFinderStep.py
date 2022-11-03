
import json
import pandas as pd
import pickle
from src.text_processing.population_tags_finder import PopulationTagsFinder
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/CropsSearchOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{MODELS_INPUTS_DIR}/search_index.pickle", "rb") as outfile:
        search_index = pickle.load(outfile)
    if config["Steps"]["PopulationTagsFinderStep"]["Apply"] == "True":
        print("PopulationTagsFinderStep", "true")
        population_tags_finder = PopulationTagsFinder()
        df = population_tags_finder.label_with_population_tags(df, search_index)
    else:
        print("PopulationTagsFinderStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/PopulationTagsFinderOutput.csv", sep=';')
