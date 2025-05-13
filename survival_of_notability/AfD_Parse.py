from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from dateutil import parser
import datetime
import requests
import re
from bs4 import BeautifulSoup
# import mwparserfromhell
import datetime
import pandas as pd
import time
import re, mwparserfromhell as mwp


from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, EXTERNAL_DATA_DIR, INTERIM_DATA_DIR

import pandas as pd
import re
import os
import warnings

warnings.filterwarnings("ignore")

app = typer.Typer()

SIG_RE = re.compile(r"""\[\[[^\]]*\]\]\s*\d{1,2}:\d{2},\s+\d{1,2}\s+\w+\s+\d{4}\s+\(UTC\).*?$""",re.X | re.S)
WP_TAG = re.compile(r'WP:\w+')

def process_text(pp):
    tokens =pp.strip_code()

    WP_tag=set(WP_TAG.findall(pp.strip_code()))

    tokens= set(tokens.split())
    
    return (tokens & BIO_TAGS) | (WP_tag & BIO_TAGS)
    

def clean_comment_keep_links(raw: str) -> str:
    """Return plain text with URLs preserved as 'title (url)' or just 'url'."""
    txt  = raw.lstrip('*').lstrip()          # drop leading bullet
    code = mwp.parse(txt)

    # 1️⃣  Convert each ExternalLink node to readable text that embeds the URL
    for link in code.filter_external_links(recursive=True):
        if link.title:                       # e.g.  [http://foo.com Title]
            replacement = f"{link.title} ({link.url})"
        else:                                # bare  [http://foo.com]
            replacement = str(link.url)
        code.replace(link, replacement)

    # 2️⃣  Strip the remaining markup
    txt = code.strip_code(normalize=True, collapse=True)

    # 3️⃣  Remove user signature + timestamp
    txt = SIG_RE.sub('', txt).strip()
    return txt


def get_afds(titles): 
    data=[]
    tags=set()
    WP_TAG = re.compile(r'WP:\w+')
    
    try:
        response = requests.get(
                    'https://en.wikipedia.org/w/api.php',
                    params={
                        'action': 'query',
                        'format': 'json',
                        'titles': titles,
                        'prop': 'revisions',
                        'rvprop': 'content'
                    }).json()

        page = next(iter(response['query']['pages'].values()))

        wikicode = page['revisions'][0]['*']
#         print(wikicode)

        parsed_wikicode = wikicode
#     mwparserfromhell.parse(wikicode)

    except: 
        return data


    month_map={'January':1, 'February':2,'March':3, 'April':4, 'May':5, 'June': 6, 'July':7, 
                      'August':8, 'September':9,'October':10, 'November':11, 'December':12}




    prev_user="none"
    first_comment=0

    for p in parsed_wikicode.split("\n"):
        pp =p



        reply=0
        action= "comment"
        recommend="none"
        user = "none"
        time="none"
        date="none"
        timestamp=0
        parent = "none"
        topic=""
        parsed_text=""
        
        try:
            while pp.find(':')==0:

                reply +=1
                pp = pp[1:]



            if pp.find("[[User:")!=-1 and pp.find("(UTC)")!=-1:
                if pp.find('Wikipedia:WikiProject Deletion sorting')>0:
                    topic=mwparserfromhell.parse(pp).strip_code().split('list of ')[1].split(" ")[0]
#                     print(topic)

                if first_comment==0:
                    action='Outcome'
                    recommend = pp.split("'''")[1] 
                    
                elif first_comment==1:
                     action='Nomination'
                        
                else:    
                    if pp.find("'''") in [0,1]:

                        recommend = pp.split("'''")[1]
    #                     print(pp)
                        if recommend.lower()!='comment':
                            action='vote'
                first_comment +=1

                if reply>0:
                    parent=prev_user
                    action="reply"

                res = [iii for iii in range(len(pp)) if pp.startswith('[[User:', iii)]
                indx = res[-1]

                user = pp[indx:].split("[[User:")[1].split("|")[0]
                time_date = pp[indx:].split("]] ([[")[-1].split("]])")[-1].split(",")

                if len(time_date)>1:
                    date= time_date[-1]
                    date = date[:date.find('(UTC)')]

                    time= time_date[-2].split(" ")[-1]
                    if date!='none':
                        date_split=date.split(' ')
                        time_split = time.split(':')

                        timestamp = datetime.datetime(int(date_split[-2]), int(month_map[date_split[-3]]), int(date_split[-4]), int(time_split[0]), int(time_split[1])).strftime('%s')
                        timestamp=int(timestamp)

                parsed_text = clean_comment_keep_links(pp)
                WP_tag=list(set(WP_TAG.findall(pp)))
        except:
            pass
        if user!="none" and timestamp!=0:
            data.append([user,action,recommend,parent,reply,time,date,timestamp,parsed_text,topic,WP_tag])
        prev_user=user +"_" +str(timestamp)
            



                    

    return data
            




def extract_AfD_logs(input_path_wikidata_nominated,output_path_conv_afd):
    df = pd.read_csv(input_path_wikidata_nominated, index_col=False)
    pd.DataFrame([['user','action','recommend','parent','reply','time','date','timestamp','rationals','topic','WP_tags','Entry','AfD Archive Link']]).to_csv(output_path_conv_afd,
                                                        mode='a',
                                                        index=False,
                                                        header=False
                                                        )
    # print(list(df['page_title']))


    for titles in tqdm(list(df['page_title'])):
        INDEX_URI2 = 'Wikipedia:Articles for deletion/' + titles
        print(INDEX_URI2)
        columns1=['user','action','recommend','parent','reply','time','date','timestamp','rationals','topic','WP_tags']
        data=get_afds(INDEX_URI2)
        if len(data)>0:
                    df_data=pd.DataFrame(data, columns=columns1)
                    df_data['Entry']=titles
                    df_data['AfD Archive Link']=INDEX_URI2
                    df_data=df_data.sort_values(by='timestamp')
                    print(df_data)
                    df_data.to_csv(output_path_conv_afd,
                                                        mode='a',
                                                        index=False,
                                                        header=False
                                                        )
                    time.sleep(.1)

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path_wikidata_nominated: Path = RAW_DATA_DIR / "Wikidata/Wikidata_Gender_Birth_Death_nominated.csv",
    output_path_conv_afd= RAW_DATA_DIR / "From_Begin_Afd_Conversation3.csv",
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    logger.info("Extract AfD Conversations")
    extract_AfD_logs(input_path_wikidata_nominated,output_path_conv_afd)
    

    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
