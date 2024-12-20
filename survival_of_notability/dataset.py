from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR

import pandas as pd

app = typer.Typer()

def make_all_biography2(input_path,output_path):

    print("Preparation involves filtering the data as follows: a) Retain entries where the creation dates precede the nomination dates. b) Include only data pertaining to subjects identified as male or female.")
    all_biographies = pd.read_csv(input_path, index_col=False)
    all_biographies=all_biographies[all_biographies['gender']!='no data']


    print("Counting days before nomination...")
    all_biographies['days_before_nomination']=(all_biographies['rev_timestamp'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14]))) - all_biographies['creation_date_original2'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))).apply(lambda x: x.total_seconds()).apply(lambda x: x/86400)

    print("Formating creation dates...")
    all_biographies['creation_dates']=all_biographies['creation_date_original2'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))

    print("Formating nomination dates...")
    all_biographies['nomination_dates']=all_biographies['rev_timestamp'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))

    all_biographies2=all_biographies[(all_biographies['days_before_nomination']>=0)]
    all_biographies2=all_biographies2[all_biographies2['gender'].isin(['male','female'])]
    
    all_biographies2.to_csv(output_path, index= False)
    print("Done with all_biographies2!")


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "all_biographies.csv",
    output_path: Path = PROCESSED_DATA_DIR / "all_biographies2.csv",
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset...")
    make_all_biography2(input_path,output_path)
    
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
