from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from tqdm import notebook as nb
import pandas as pd
import time
from config import INTERIM_DATA_DIR, RAW_DATA_DIR
import requests
import bz2
import json
import os

app = typer.Typer()

# --- Gender mapping ---
GENDER_LABELS = {
    'Q6581097': 'male',
    'Q6581072': 'female',
    'Q1097630': 'transgender female',
    'Q2449503': 'transgender male',
    'Q48270': 'non-binary',
    'Q15978631': 'genderqueer',
    'Q1052281': 'intersex'
}

# --- Process dump sequentially ---
def extract_itwiki_humans_sequential(dump_path, output_path, pageid_title_csv):
# Load your page_id and page_title list
    page_df = pd.read_csv(pageid_title_csv, index_col=False)
    page_df.columns = ["page_id", "page_title", "Entry", "creation_timestamp"]
    title_set = list(page_df['Entry'])
    # print(title_set)

    print(f"✅ Loaded {len(title_set)} titles from your page list.")

    all_results = []

    HUMAN_QID = "Q5"
    P_INSTANCE_OF = "P31"
    P_GENDER = "P21"
    P_BIRTH = "P569"
    P_DEATH = "P570"

    with bz2.open(dump_path, 'rt') as file:
        pbar = tqdm(total=os.path.getsize(dump_path), desc="Processing Dump", unit_scale=True, unit="B")

        for line in file:
            if not line.startswith('{'):
                pbar.update(len(line.encode('utf-8')))
                continue

            line = line.rstrip(',\n')
            try:
                entity = json.loads(line)
            except json.JSONDecodeError:
                pbar.update(len(line.encode('utf-8')))
                continue

            qid = entity.get('id')
            claims = entity.get('claims', {})
            sitelinks = entity.get('sitelinks', {})

            # Must have itwiki sitelink recorded
            itwiki_link = sitelinks.get('itwiki')
            if not itwiki_link:
                pbar.update(len(line.encode('utf-8')))
                continue

            # Must be instance of human
            if P_INSTANCE_OF in claims:
                is_human = any(
                    claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id') == HUMAN_QID
                    for claim in claims[P_INSTANCE_OF]
                    if claim.get('mainsnak', {}).get('datatype') == 'wikibase-item'
                )
                if not is_human:
                    pbar.update(len(line.encode('utf-8')))
                    continue
            else:
                pbar.update(len(line.encode('utf-8')))
                continue

            # Get page title
            itwiki_title = itwiki_link.get('title')
            # print(itwiki_title)

            # Is this title inside your given biography list?
            in_biography_list = itwiki_title in title_set

            # Strictly get only Italian label
            label_it = entity.get('labels', {}).get('it', {}).get('value')
            item_label = label_it if label_it else ''

            gender = None
            birth = None
            death = None

            if P_GENDER in claims:
                gender_claim = claims[P_GENDER][0]
                gender_qid = gender_claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                gender = GENDER_LABELS.get(gender_qid, gender_qid)

            if P_BIRTH in claims:
                birth_claim = claims[P_BIRTH][0]
                raw_birth = birth_claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
                if raw_birth:
                    birth = raw_birth.lstrip('+').split('T')[0]

            if P_DEATH in claims:
                death_claim = claims[P_DEATH][0]
                raw_death = death_claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
                if raw_death:
                    death = raw_death.lstrip('+').split('T')[0]

# page_title,Entry,QID,gender,date_of_birth,date_of_death,in_biography_list

            # all_results.append({
            #     'page_title': itwiki_title,
            #     'Entry': item_label,
            #     'QID': qid,
            #     'gender': gender,
            #     'date_of_birth': birth,
            #     'date_of_death': death,
            # })

            # print(all_results)
            pd.DataFrame([[itwiki_title.replace(" ", "_"), item_label,  qid, gender, birth, death, in_biography_list]]).to_csv(output_path, 
                                                            mode='a', 
                                                            index=False,
                                                            header=False
                                                           )

            pbar.update(len(line.encode('utf-8')))

        pbar.close()

    # df = pd.DataFrame(all_results)
    # df.to_csv(output_csv, index=False)
    # print(f"✅ Saved {len(df)} rows to {output_csv}")
    # return df


        
    

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = INTERIM_DATA_DIR / "latest-all.json.bz2",
    output_path: Path = INTERIM_DATA_DIR / "extracted_wikidata_all.csv",
    list_bio: Path = RAW_DATA_DIR / "Quarry/Wikiproject_Bio2_creation_dates.csv"
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Extracting wikidata items...")

    extract_itwiki_humans_sequential(input_path, output_path, list_bio)

    

    # -----------------------------------------


if __name__ == "__main__":
    app()
