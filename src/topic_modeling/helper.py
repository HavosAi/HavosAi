import pandas as pd
from IPython.display import display


# always display all columns of a pandas.DataFrame
pd.set_option('display.max_columns', None)

# enrich pandas.DataFrame with `explore` method
def explore(df):
    print(f'DF shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    display(df.head())
pd.DataFrame.explore = explore
