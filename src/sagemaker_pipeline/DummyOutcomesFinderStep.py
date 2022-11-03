
import json
import pandas as pd
from src.sagemaker_pipeline.constants import CONFIG_INPUTS_DIR, INPUTS_DIR, OUTPUTS_DIR

  
if __name__ == "__main__":
    with open(f"{CONFIG_INPUTS_DIR}/config.json", "r") as file:
        config = json.load(file)
        print("file config.json: ", config)
#     with open(f"{CONFIG_OUTPUTS_DIR}/config.json", "w") as file:
#         json.dump(config, file)
    df = pd.read_csv(
        f"{INPUTS_DIR}/OutcomesFinderOutput.csv",
        sep=';'
    )
    if config["Steps"]["DummyOutcomesFinderStep"]["Apply"] == "True":
        print("DummyOutcomesFinderStep", "true")
    else:
        print("DummyOutcomesFinderStep", "false")
    print(f'Dummy Outcomes finder. Saving df to {OUTPUTS_DIR}/DummyOutcomesFinderOutput')
    df.to_csv(f"{OUTPUTS_DIR}/DummyOutcomesFinderOutput.csv", sep=';')
    print(f'Dummy Outcomes finder. Saved df.')
