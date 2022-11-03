
import json
import pandas as pd
import pickle
from src.text_processing.advanced_text_normalization import AdvancedTextNormalizer
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, MODELS_INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/SearchIndexOutput.csv",
        sep=';',
        index_col=0,
    )

    with open(f"{MODELS_INPUTS_DIR}/abbreviation_resolver.pickle", "rb") as outfile:
        abbreviations_resolver = pickle.load(outfile)
    if config["Steps"]["AdvancedTextNormalizerStep"]["Apply"] == "True":
        print("AdvancedTextNormalizerStep", "true")
        advanced_text_normalizer = AdvancedTextNormalizer(abbreviations_resolver)
        df = advanced_text_normalizer.normalize_text_for_df(df)
    else:
        print("AdvancedTextNormalizerStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/AdvancedTextNormalizerOutput.csv", sep=';')
