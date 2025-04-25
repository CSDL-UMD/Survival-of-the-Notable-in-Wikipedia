from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from tqdm import notebook as nb
import pandas as pd
import time
from config import INTERIM_DATA_DIR, RAW_DATA_DIR
import requests

app = typer.Typer()

def get_qid_label_and_creation_by_pageid(input_path, output_path,lang='en'):

    input= pd.read_csv(input_path, index_col=False)
    input = input.rename(columns={'title':'page_title', 'pageid':'page_id'})
    input = input[['page_title','page_id']]
    print(input.head())
    list_output = []
    for i,row in tqdm(input[2000:2050].iterrows(), total= len(input)):
        page_id = int(row['page_id'])
        try:
            # Step 1: Get from Wikipedia — title, QID, creation timestamp
            wiki_response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "pageids": page_id,
                    "prop": "revisions|pageprops",
                    "rvdir": "newer",  # Oldest = creation
                    "rvlimit": 1,
                    "rvprop": "timestamp"
                },
                timeout=10
            ).json()

            page = next(iter(wiki_response['query']['pages'].values()))
            timestamp = page['revisions'][0]['timestamp'] if "revisions" in page else "No data"

            qid = page.get("pageprops", {}).get("wikibase_item", "")

            

        except Exception as e:
            print(f"❌ Error fetching for page_id {page_id}: {e}")
            pass

        # print([page_id, row['page_title'], label, timestamp])
        pd.DataFrame([[page_id, row['page_title'],  row['page_title'].replace("_", " "), timestamp]]).to_csv(output_path, 
                                                            mode='a', 
                                                            index=False,
                                                            header=False
                                                           )
        # list_output.append([page_id, row['page_title'], label, timestamp])
        # time.sleep(0.1)
        
    

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = INTERIM_DATA_DIR / "Wikiproject_Bio.csv",
    output_path: Path = RAW_DATA_DIR / "Quarry/Wikiproject_Bio2_creation_dates.csv",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Generating features from dataset...")
    
    get_qid_label_and_creation_by_pageid(input_path,output_path)

    # -----------------------------------------


if __name__ == "__main__":
    app()
