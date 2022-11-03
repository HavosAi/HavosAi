
import json
import pandas as pd
from src.text_processing.keywords_normalizer import KeywordsNormalizer
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
        f"{INPUTS_DIR}/AdvancedTextNormalizerOutput.csv",
        sep=';',
        index_col=0,
    )

    if config["Steps"]["KeywordsNormalizerStep"]["Apply"] == "True":
        print("KeywordsNormalizerStep", "true")
        # no column "identificators" in `key_words_column_names`, as we couldn't find it
        df = KeywordsNormalizer().normalize_key_words(df, key_words_column_names=["keywords",])
    else:
        print("KeywordsNormalizerStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/KeywordsNormalizerOutput.csv", sep=';')
