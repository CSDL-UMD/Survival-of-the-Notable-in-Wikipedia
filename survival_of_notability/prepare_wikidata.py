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
import urllib.parse

app = typer.Typer()

def prepare_all_wikidata(input_path, input_path_creation,input_nominated,output_path_all,output_path_nominated,output_path_need_creation,output_path_need_wikidata):
    df = pd.read_csv(input_path, index_col=False)
    df['page_title'] = df['sitelink'].apply(lambda x: str(x).split('/')[-1]).apply(lambda x: urllib.parse.unquote(x))
    df['QID'] = df['item'].apply(lambda x: str(x).split('/')[-1])
    df2=df[['page_title','label','QID','Gender','birth','death']].fillna('No data').rename(columns={'label':'Entry','Gender':'gender','birth':'date_of_birth','death':'date_of_death'})
    
    # print(df2)

    df_creation = pd.read_csv(input_path_creation, index_col=False)
    
    print(len(df_creation))

    df_creation.columns = ["page_id", "page_title", "Entry", "creation_timestamp"]
    merge_all=pd.merge(df_creation,df2, on='page_title',how='outer', indicator=True).drop_duplicates(subset='page_title')
    need_data_creation = merge_all[merge_all['_merge']=='right_only']['page_title']
    need_data_wikidata = merge_all[merge_all['_merge']=='left_only']['page_title']
    need_data_creation.to_csv(output_path_need_creation, index=False)
    need_data_wikidata.to_csv(output_path_need_wikidata, index=False)


    merge_all2 = merge_all[merge_all['_merge']=='both']
    merge_all2 = merge_all2[['page_id','page_title','Entry_y','QID','gender','date_of_birth','date_of_death']]
    merge_all2.columns = ['page_id','page_title','Entry','QID','gender','date_of_birth','date_of_death']
    # [['page_id','page_title','Entry_x','QID','gender','date_of_birth','date_of_death']]
    print("missng creation dates: ", len(need_data_creation)," missing wikidata: ",len(need_data_wikidata))
    print(merge_all2)
    merge_all2.to_csv(output_path_all, index=False)

    df_nomination = pd.read_csv(input_nominated, index_col=False)
    df_nomination.columns = ["page_title", "rev_timestamp"]
    df_nomination_merge_human=pd.merge(df_nomination,df2, on='page_title', how = 'inner').drop_duplicates(subset='page_title')
    df_nomination_merge_human['instance of']='human'
    df_nomination_merge_human =df_nomination_merge_human[['Entry','page_title','QID','instance of','gender','date_of_birth','date_of_death']]
    print(df_nomination_merge_human)
    print(len(df_nomination_merge_human)/len(df_creation))
    df_nomination_merge_human.to_csv(output_path_nominated, index=False)
    print(df_nomination[~df_nomination['page_title'].isin(df_nomination_merge_human['page_title'])])
    need_wikidata2= df_nomination[~df_nomination['page_title'].isin(df_nomination_merge_human['page_title'])]
    need_wikidata_all=pd.concat([need_data_wikidata,need_wikidata2['page_title']])

    need_wikidata_all.to_csv(output_path_need_wikidata, index=False)


        
    

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = INTERIM_DATA_DIR / "wikidata_it.csv",
    input_path_creation: Path = RAW_DATA_DIR / "Quarry/Wikiproject_Bio2_creation_dates.csv",
    input_nominated: Path = RAW_DATA_DIR / "Quarry/All_AfDs_3_April_4_25.csv",
    output_path_all: Path = RAW_DATA_DIR / "Wikidata/wikidata_page_id_all2_merged.csv",
    output_path_nominated: Path = RAW_DATA_DIR / "Wikidata/Wikidata_Gender_Birth_Death_nominated.csv",
    output_path_need_creation: Path = INTERIM_DATA_DIR / "need_creation.csv",
    output_path_need_wikidata: Path = INTERIM_DATA_DIR / "need_wikidata.csv"

    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Prepare all wikidata items...")

    prepare_all_wikidata(input_path, input_path_creation,input_nominated,output_path_all,output_path_nominated,output_path_need_creation,output_path_need_wikidata)

    

    # -----------------------------------------


if __name__ == "__main__":
    app()
