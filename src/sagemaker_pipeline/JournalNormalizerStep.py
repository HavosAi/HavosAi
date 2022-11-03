
import json
import pandas as pd
from src.text_processing.journal_normalizer import JournalNormalizer
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, OUTPUTS_DIR

  
if __name__ == "__main__":
    
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
        
    df = pd.read_csv(
            f"{INPUTS_DIR}/KeywordsNormalizerOutput.csv",
        sep=';',
        index_col=0,
    )
    
    if config["Steps"]["JournalNormalizerStep"]["Apply"] == "True":
        print("JournalNormalizerStep", "true")
        df = JournalNormalizer().correct_journal_names(df, journal_column="journal_name")
    else:
        print("JournalNormalizerStep", "false")
    df.to_csv(f"{OUTPUTS_DIR}/JournalNormalizerOutput.csv", sep=';')
