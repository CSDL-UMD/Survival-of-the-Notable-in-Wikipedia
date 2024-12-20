from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, EXTERNAL_DATA_DIR

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

app = typer.Typer()

def data_part2(part_2,petscan_path):
    logger.info("Part 2: Set up and correct the data, ensuring entries with a birth date but no death date are properly handled...\n")
    print("Removing data with wrong date of birth...\n")
    part_2['wrong']=part_2.apply(lambda row: 1 if int(str(row['creation_date_original2'])[:4])< row['birth'] else 0,axis=1)
    part_2=part_2[part_2['wrong']==0]
    part_2=part_2.drop(columns=['wrong'])

    print("Identifying people born before 1907...\n")
    part_2C=part_2[part_2['birth']<1907]
    part_2C['Alive']=0

    print("Identifying people born after 1907 and alive...\n")
    part_2_notC = part_2[part_2['birth']>=1907]
    part_2A = part_2_notC[part_2_notC['BLP']==1]
    part_2A['Alive']=1

    print("Identifying people born after 1907 and deceased...\n")
    part_2B = part_2_notC[part_2_notC['BLP']==0]
    dead=pd.read_csv(petscan_path / "Dead_people_all.csv",on_bad_lines='skip', index_col=False)
    part_2B_a=part_2B[part_2B['page_title'].isin(dead['title'])].drop_duplicates(subset='page_title', keep='first')
    part_2B_a['Alive']=0
    part_2B_b=part_2B[~part_2B['page_title'].isin(dead['title'])].drop_duplicates(subset='page_title', keep='first')
    part_2B_b['Alive']=1

    part_2=pd.concat([part_2A,part_2B_a,part_2B_b,part_2C])
    print("Done with Part 2!\n")
    return part_2

def data_part1(part_1):
    logger.info("Part 1: Set up and process the data, focusing on entries that include a recorded date of death....\n")
    part_1['Alive']=0

    print("Splitting data based on availbility of date of birth...\n")
    part_1A=part_1[part_1['birth']!='no data']
    part_1B=part_1[part_1['birth']=='no data']

    print("Removing data with wrong date of birth...\n")
    part_1A['wrong']=part_1A.apply(lambda row: 1 if int(str(row['creation_date_original2'])[:4])< row['birth'] else 0,axis=1)
    part_1A=part_1A[part_1A['wrong']==0]
    part_1A=part_1A.drop(columns=['wrong'])

    print("Identifying date of birth of the people who are dead...\n")
    part_1B['birth']=part_1B['death'].apply(lambda x: x-70)

    part_1=pd.concat([part_1A,part_1B])

    print("Identifying the living people at the time of nomination who are deceased after 2000...\n")
    part_1_after2000=part_1[part_1['death']>=2000]
    part_1_before2000=part_1[part_1['death']<2000]
    part_1_after2000['Alive']=part_1_after2000.apply(lambda row: 1 if pd.to_datetime(row['nomination_dates'],utc=True)< pd.to_datetime(str(row['death']).replace("+",""), utc=True) else 0,axis=1)



    part_1=pd.concat([part_1_before2000,part_1_after2000])
    print("Done with Part 1!")

    return part_1

def make_data_for_survival_model(petscan_path,output_path_kmf):
    print("Loading list of Living People...\n")
    BLP=pd.read_csv(petscan_path / "Living_people.csv", index_col=False)
    BLP=BLP[['title']]
    all_biographies2 = pd.read_csv(output_path_kmf, index_col=False)

    print("Merging All biographies with Living people...\n")
    all_biographies2_BLP=pd.merge(all_biographies2,BLP, left_on='page_title',right_on='title', how='left')
    all_biographies2_BLP['BLP']= all_biographies2_BLP['title'].fillna(0)
    all_biographies2_BLP['Entry2']=all_biographies2_BLP['Entry'].apply(lambda x: x.replace(" ","_"))
    all_biographies2_BLP.loc[all_biographies2_BLP[(all_biographies2_BLP['Entry2'].isin(BLP['title'])) & (all_biographies2_BLP['BLP']==0)].index,'BLP'] =1
    all_biographies2_BLP.loc[all_biographies2_BLP['BLP']!=0,'BLP']=1


    print("Recoding Gender covariate...\n")
    all_biographies2_BLP.loc[all_biographies2_BLP['gender']=='female','Female']=1
    all_biographies2_BLP.loc[all_biographies2_BLP['gender']!='female','Female']=0


    print("Formating date of birth and death...\n")
    all_biographies2_BLP['birth']=all_biographies2_BLP['date_of_birth'].apply(lambda x: -1*int(x.split('-')[1]) if x[0]=='-' else( int(x.split('-')[0] ) if len(x.split('-')[0])==4 else ( int(x.split('-')[0]) if x[0]=='+' else 'no data') ) )
    all_biographies2_BLP['death']=all_biographies2_BLP['date_of_death'].apply(lambda x: -1*int(x.split('-')[1]) if x[0]=='-' else( int(x.split('-')[0] ) if len(x.split('-')[0])==4 else ( int(x.split('-')[0]) if x[0]=='+' else 'no data') ) )


    print("Splitting dataset based on the availability of dates of birth and death\n")
    part_1=all_biographies2_BLP[all_biographies2_BLP['death']!='no data']
    part_2=all_biographies2_BLP[(all_biographies2_BLP['birth']!='no data') & (all_biographies2_BLP['death']=='no data')]
    part_3=all_biographies2_BLP[(all_biographies2_BLP['birth']=='no data') & (all_biographies2_BLP['death']=='no data')]
    print("Data is splitted in 3 parts!\n")

    part_1 = data_part1(part_1)
    part_2 = data_part2(part_2, petscan_path)


def make_all_biography2(input_path,output_path_kmf):

    logger.info("Preparation involves filtering the data as follows: a) Retain entries where the creation dates precede the nomination dates. b) Include only data pertaining to subjects identified as male or female.")
    all_biographies = pd.read_csv(input_path, index_col=False)
    all_biographies=all_biographies[all_biographies['gender']!='no data']


    print("Counting days before nomination...\n")
    all_biographies['days_before_nomination']=(all_biographies['rev_timestamp'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14]))) - all_biographies['creation_date_original2'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))).apply(lambda x: x.total_seconds()).apply(lambda x: x/86400)

    print("Formating creation dates...\n")
    all_biographies['creation_dates']=all_biographies['creation_date_original2'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))

    print("Formating nomination dates...\n")
    all_biographies['nomination_dates']=all_biographies['rev_timestamp'].apply(str).apply(lambda x: pd.Timestamp(int(x[:4]),int(x[4:6]),int(x[6:8]),int(x[8:10]),int(x[10:12]),int(x[12:14])))

    all_biographies2=all_biographies[(all_biographies['days_before_nomination']>=0)]
    all_biographies2=all_biographies2[all_biographies2['gender'].isin(['male','female'])]
    
    all_biographies2.to_csv(output_path_kmf, index= False)
    print("Done with all_biographies2!")


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "all_biographies.csv",
    output_path_kmf: Path = PROCESSED_DATA_DIR / "all_biographies2.csv",
    petscan_path: Path = EXTERNAL_DATA_DIR 
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset for Kaplan-Meier estimation...")
    make_all_biography2(input_path,output_path_kmf)

    logger.info("Processing dataset for Cox proportional hazards model...")
    make_data_for_survival_model(petscan_path,output_path_kmf)
    
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
