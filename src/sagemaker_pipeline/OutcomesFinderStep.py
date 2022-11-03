
import json
import pandas as pd
from src.text_processing.all_column_filler import AllColumnFiller
from src.sagemaker_pipeline.constants import  CONFIG_INPUTS_DIR, INPUTS_DIR, OUTPUTS_DIR, OUTCOMES_MODEL


if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
#     with open(f"{CONFIG_OUTPUTS_DIR}/config.json", "w") as file:
#         json.dump(config, file)
    df = pd.read_csv(
        f"{INPUTS_DIR}/ProgramExtractorOutput.csv",
        sep=';',
        index_col=0,
    )    
    if config["Steps"]["OutcomesFinderStep"]["Apply"] == "True":
        print("OutcomesFinderStep", "true")
        column_info = dict()
        column_info["model_folder"] = OUTCOMES_MODEL
        all_column_filler = AllColumnFiller()
        df = all_column_filler.fill_outcomes(df, None, None, column_info)
    else:
        print("OutcomesFinderStep", "false")
    print(f'Outcomes finder. Saving df to {OUTPUTS_DIR}/OutcomesFinderOutput.csv')
    df.to_csv(f"{OUTPUTS_DIR}/OutcomesFinderOutput.csv", sep=';')
    print(f'Outcomes finder. Saved df.')
