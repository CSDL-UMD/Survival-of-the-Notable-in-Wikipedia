from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from tqdm import notebook as nb
import pandas as pd
import time
from config import INTERIM_DATA_DIR, RAW_DATA_DIR
import requests
from deep_translator import GoogleTranslator
import re

app = typer.Typer()
GENDER_LABELS = {
    'Q6581097': 'male',
    'Q6581072': 'female',
    'Q1097630': 'transgender female',
    'Q2449503': 'transgender male',
    'Q48270': 'non-binary',
    'Q15978631': 'genderqueer',
    'Q1052281': 'intersex'
}


def get_sitelinks_from_itwiki_title(title):
    """Get Wikidata QID and sitelinks for all languages given an enwiki title."""
    try:
        response = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbgetentities",
                "sites": "enwiki",
                "titles": title,
                "props": "sitelinks",
                "format": "json"
            }
        ).json()
        entity = next(iter(response.get("entities", {}).values()))
        qid = entity.get("id")
        sitelinks = entity.get("sitelinks", {})
        return qid, sitelinks
    except Exception:
        return None, {}

def query_qid_and_pageid_from_title(title, lang):
    """Try to get QID and page_id from a title in a given language Wikipedia."""
    try:
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "pageprops",
                "titles": title,
                "format": "json"
            }
        ).json()
        page = next(iter(response['query']['pages'].values()))
        qid = page.get("pageprops", {}).get("wikibase_item")
        page_id = page.get("pageid") if qid else None
        return qid, page_id
    except Exception:
        return None, None

def get_qid_with_fallback(title, fallback_langs):

    
    """Try itwiki, then fallback langs using translated sitelinks."""
    qid, page_id = query_qid_and_pageid_from_title(title, "en")
    if qid:
        return qid, "en", page_id

    # Try sitelinks fallback
    qid, sitelinks = get_sitelinks_from_itwiki_title(title)
    if not qid:
        return None, None, "not found"

    print(title)
    for lang in fallback_langs:
        key = f"{lang}wiki"
        # translated_title = GoogleTranslator(source='auto', target=lang).translate(title)
        translated_title = sitelinks[key]['title']
        print(translated_title)
        qid_check, _ = query_qid_and_pageid_from_title(translated_title, lang)
        if qid_check:
            return qid_check, lang, "not found"

    return None, None, "not found"

# ========== Wikidata Info Extraction ==========

def get_wikidata_info(qid):
    """Fetch label, gender, birth, death if item is a human (P31 = Q5)."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    try:
        data = requests.get(url).json()
        entity = data['entities'][qid]
        claims = entity.get('claims', {})

        # === Check if instance of human ===
        is_human = any(
            c.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id') == 'Q5'
            for c in claims.get("P31", [])
            if c.get('mainsnak', {}).get('datatype') == 'wikibase-item'
        )
        if not is_human:
            return None

        label = entity.get('labels', {}).get('en', {}).get('value') or \
                entity.get('labels', {}).get('en', {}).get('value', '')

        def extract_claim(pid):
            if pid in claims:
                val = claims[pid][0].get('mainsnak', {}).get('datavalue', {}).get('value')
                if isinstance(val, dict) and 'id' in val:
                    return val['id']
                elif isinstance(val, dict) and 'time' in val:
                    return val['time'].lstrip('+').split('T')[0]
            return "No data"

        gender_qid = extract_claim("P21")
        birth = extract_claim("P569")
        death = extract_claim("P570")

        # Resolve gender label
        gender = ""
        if gender_qid:
            # gdata = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{gender_qid}.json").json()
            # gender = gdata['entities'][gender_qid].get('labels', {}).get('en', {}).get('value', '')
            gender = GENDER_LABELS.get(gender_qid, gender_qid)


        return {
            "item": f"https://www.wikidata.org/entity/{qid}",
            "label": label,
            "gender": gender,
            "birth": birth,
            "death": death
        }

    except Exception as e:
        print(f"❌ Error fetching {qid}: {e}")
        return None

# ========== Main Script ==========

def get_wikidata(input_csv, output_path_all,output_path_nominated, fallback_langs=None):
    if fallback_langs is None:
        fallback_langs = ["en", "it","de", "fr", "es", "ru", "ja", "nl", "pl", "pt", "ar"]

    df = pd.read_csv(input_csv)
    titles = df['page_title'].dropna().unique()

    results = []

    for title in tqdm(titles, desc="Processing titles"):
        title = re.sub(r'\\([A-Za-z0-9_]+)"', r'"\1"', title)
    
    # Also fix any remaining \word\" or \word\""
        title = re.sub(r'\\([A-Za-z0-9_]+)\\?"{1,2}', r'"\1"', title)

        if title.endswith('"') and title.count('"') % 2 != 0:
            title = title[:-1]

        # print(title)
        qid, lang_used, page_id = get_qid_with_fallback(title, fallback_langs)
        if qid:
            info = get_wikidata_info(qid)
            if info:
                info.update({
                    "page_title": title,
                    "qid": qid,
                    "language": lang_used,
                    "page_id": page_id,
                    "instance of": 'human'
                })
                # print(info)
                if info['page_id'] != "not found":
                    # page_id,page_title,Entry,QID,gender,date_of_birth,date_of_death
                    print(info['page_id'],info['page_title'],info['label'],info['qid'],info['gender'],info['birth'],info['death'])
                    pd.DataFrame([[info['page_id'],info['page_title'],info['label'],info['qid'],info['gender'],info['birth'],info['death']]]).to_csv(output_path_all, 
                                                            mode='a', 
                                                            index=False,
                                                            header=False
                                                           )
                else:
                    # Entry,page_title,QID,instance of,gender,date_of_birth,date_of_death
                    print(info['label'],info['page_title'],info['qid'],info['instance of'],info['gender'],info['birth'],info['death'])    
                    pd.DataFrame([[info['label'],info['page_title'],info['qid'],info['instance of'],info['gender'],info['birth'],info['death']]]).to_csv(output_path_nominated, 
                                                            mode='a', 
                                                            index=False,
                                                            header=False
                                                           )
                # results.append(info)
                time.sleep(0.1)
                continue

        # # If no QID or not human
        # results.append({
        #     "page_title": title,
        #     "qid": qid,
        #     "language": lang_used,
        #     "page_id": page_id,
        #     "item": None,
        #     "label": None,
        #     "gender": None,
        #     "birth": None,
        #     "death": None
        # })
        time.sleep(0.3)

    # pd.DataFrame(results).to_csv(output_csv, index=False)
    # print(f"✅ Done. Saved to {output_csv}")
        
    

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = INTERIM_DATA_DIR / "need_wikidata.csv",
    input_path_already_create: Path = RAW_DATA_DIR / "Quarry/Wikiproject_Bio2_creation_dates.csv",
    output_path_all: Path = RAW_DATA_DIR / "Wikidata/wikidata_page_id_all2_merged.csv",
    output_path_nominated: Path = RAW_DATA_DIR / "Wikidata/Wikidata_Gender_Birth_Death_nominated.csv",
    output_path_needed_create: Path = INTERIM_DATA_DIR / "need_creation.csv"
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Generating features from dataset...")
    
    get_wikidata(input_path,output_path_all,output_path_nominated)
    df_create = pd.read_csv(input_path_already_create, index_col = False)
    df_create.columns = ["page_id", "page_title", "Entry", "creation_timestamp"]
    titles = df_create['page_title']

    df_nominated = pd.read_csv(output_path_nominated, index_col = False)
    needed_titles=df_nominated[~df_nominated['page_title'].isin(titles)]['page_title']
    needed_titles.to_csv(output_path_needed_create,mode='a', index=False,header=False)
    # print(needed_titles)


    # -----------------------------------------


if __name__ == "__main__":
    app()
