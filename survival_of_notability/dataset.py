from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
# import tqdm.notebook as nb


from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, EXTERNAL_DATA_DIR

import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')

app = typer.Typer()

def word_count(str):
    counts = dict()
    words = str.split()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return list(counts.values())

def extract_feature_for_competing_risk(afds_all,all_biographies2_with_data):
    print("Extracting features for competing risk analysis...\n")

    
    groups=afds_all.groupby('page_title')

    features_del=[]

    for i,g in tqdm(groups):
        # print(i)

        target= g.sort_values(by='timestamp')
        # print((pd.Timestamp(target.iloc[-1]['timestamp'], unit='s')-pd.Timestamp(all_biographies2_with_data[all_biographies2_with_data['page_title']==i]['nomination_dates'].iloc[0])).total_seconds())

        num_users=num_messages=num_words=num_seconds=0
        try:
            if len(target)>0:
                num_users = len(target['user'].unique()) +1
                num_messages = len(target)+1
                ave_num_words = (sum(target['rationals'].apply(lambda x: word_count(str(x))).sum())/(num_messages-1))+1
                num_seconds=(pd.Timestamp(target.iloc[-1]['timestamp'], unit='s')-pd.Timestamp(target.iloc[0]['timestamp'], unit='s')).total_seconds()

                if num_seconds==0:
                    # print(i[0])
                    # print(all_biographies2_with_data[all_biographies2_with_data['page_title']==i])
                    num_seconds=(pd.Timestamp(target.iloc[-1]['timestamp'], unit='s')-pd.Timestamp(all_biographies2_with_data[all_biographies2_with_data['page_title']==i]['nomination_dates'].iloc[0])).total_seconds()

            features_del.append([i, num_seconds,num_users,num_messages,ave_num_words])
        except:
            pass



    df_features_del=pd.DataFrame(features_del,columns=['page_title','num_seconds','num_users','num_messages','ave_num_words'])
    df_features_del=df_features_del[df_features_del['num_seconds']>0]
    return df_features_del


def parse_and_clean_outcomes(all_biographies2_with_data,df_features_del, afds_all ):
    print("Organizing all data for competing risk analysis...\n")
    data_for_compete_risk=all_biographies2_with_data[['QID','page_title','creation_dates', 'nomination_dates','days_before_nomination','nominated','Gender', 'Wikipedia_Age','Status']]
    data_for_compete_risk['tstart']=0
    data_for_compete_risk['tstop']=data_for_compete_risk['days_before_nomination']*86400
    data_for_compete_risk['event']=data_for_compete_risk['nominated'].apply(lambda x:'not nominated' if x==0 else 'nominated')
    data_for_compete_risk['id']=data_for_compete_risk.index
    data_for_compete_risk=data_for_compete_risk.drop_duplicates(subset='id', keep='first')


    print("Organizing data of nominated afd for competing risk analysis...\n")
    data_for_compete_risk_nominated=pd.merge(data_for_compete_risk,df_features_del, on='page_title',)[['QID','page_title','creation_dates', 'nomination_dates','days_before_nomination','nominated','Gender', 'Wikipedia_Age','Status','id','num_seconds','num_users','num_messages','ave_num_words']]
    data_for_compete_risk_nominated=data_for_compete_risk_nominated.drop_duplicates(subset='id', keep='first')
    data_for_compete_risk_nominated['tstart']=data_for_compete_risk_nominated['days_before_nomination']*86400
    data_for_compete_risk_nominated['tstop']=data_for_compete_risk_nominated['tstart'] + data_for_compete_risk_nominated['num_seconds']
    data_for_compete_risk_nominated=pd.merge(data_for_compete_risk_nominated,afds_all[afds_all['action']=='Outcome'][['page_title','recommend']],on='page_title',how='left').drop_duplicates(subset='id', keep='first')
    data_for_compete_risk_nominated = data_for_compete_risk_nominated.rename(columns={'recommend':'event'})
    data_for_compete_risk_nominated=data_for_compete_risk_nominated.drop(columns='num_seconds')

    print("Cleaning the text of outcome...\n")

    data_for_compete_risk_nominated['event2']=data_for_compete_risk_nominated['event'].apply(lambda x: str(x).lower().replace("not delete","keep").replace("delete and redirect","redirect").replace("kept","keep")).apply(lambda x: re.search(r"delete|deletion|keep|no consensus|redirect|merge|withdraw|close|speedied|moot|a7|move|inclusion",x).group(0) if bool(re.search(r"delete|deletion|keep|no consensus|redirect|merge|withdraw|close|speedied|moot|a7|move|inclusion",x))==True else x ).apply(lambda x: x.replace("<span style=\"color:red;\">","" ).replace("</span>","").replace("<font color=green>","").replace("</font>","").replace("<font color=red>","").replace("withdraw","keep").replace("kept","keep"))                                                                                
    data_for_compete_risk_nominated['event2']=data_for_compete_risk_nominated['event2'].apply(lambda x: x.replace("copyvio","delete")
                                                                                                         .replace("speedied","delete")
                                                                                                         .replace("speedy","delete")
                                                                                                         .replace("deletion","delete")
                                                                                                         .replace("a7","delete")
                                                                                                         .replace("flagged as ","")
                                                                                                         .replace("move","keep")
                                                                                                         .replace("close","keep")
                                                                                                         .replace("no concensus","no consensus")
                                                                                                         .replace("no consensus","keep")
                                                                                                         .replace("moot","keep")
                                                                                                         .replace("inclusion","keep")
                                                                                                         .replace("procedural closure","keep")
                                                                                                         .replace("userfy","keep")
                                                                                                         .replace("userfied","keep")

                                                                                             )


    data_for_compete_risk_nominated=data_for_compete_risk_nominated.drop(columns='event').rename(columns={'event2':'event'})

    print("Organizing most frequent event/outcome...\n")
    data_for_compete_risk['num_users']=0
    data_for_compete_risk['num_messages']=0
    data_for_compete_risk['ave_num_words']=0

    data_for_compete_risk_all= pd.concat([data_for_compete_risk_nominated,data_for_compete_risk[data_for_compete_risk_nominated.columns]]).fillna(0)
    list_cat=list(data_for_compete_risk_all['event'].value_counts()[:6].index)
    data_for_compete_risk_all['event']=data_for_compete_risk_all['event'].apply(lambda x: x if x in list_cat else "other")
    data_for_compete_risk_all['event']=data_for_compete_risk_all['event'].apply(lambda x: x.replace(" ","-"))
    data_for_compete_risk_all=data_for_compete_risk_all.sort_values(by='id')
    data_for_compete_risk_all=data_for_compete_risk_all[data_for_compete_risk_all['tstop']!= data_for_compete_risk_all['tstart']]
    data_for_compete_risk_all=data_for_compete_risk_all[data_for_compete_risk_all['tstop']<=8395*86400].sort_values(by='tstop')
    
    return data_for_compete_risk_all

def make_data_for_competing_risk_model(input_path_conv_afd,output_path_cox_ph,output_path_compete):
    articles = pd.read_csv(input_path_conv_afd, index_col=False)
    print("Extracting the outcome from the conversation...\n")
    articles['page_title']=articles['Entry'].apply(lambda x: str(x).replace(" ","_"))

    all_biographies2_with_data = pd.read_csv(output_path_cox_ph, index_col=False)
    afds=pd.merge(articles[articles['action']=='Outcome'][['page_title','recommend']], all_biographies2_with_data, on='page_title').drop_duplicates(subset='page_title')
    afds['outcome']=afds['recommend'].apply(lambda y: str(re.findall('delete|keep|merge|redirect|no consensus|d</span>elete|withdrawn|deletion|close|inclusion',str(y).lower(), flags=re.IGNORECASE)).replace("\'","").replace("[","").replace("]",""))

    afds_all=pd.merge(afds[['page_title','outcome']], articles[articles['timestamp']!=-1], on='page_title')
    afds_all['recommend']=afds_all['recommend'].apply(lambda x: str(x).lower())
    df_features_del = extract_feature_for_competing_risk(afds_all,all_biographies2_with_data)
    data_for_compete_risk_all = parse_and_clean_outcomes(all_biographies2_with_data,df_features_del,afds_all)


    data_for_compete_risk_all.to_csv(output_path_compete, index=False)




def data_part3(part_3,petscan_path):
    print("Identifying living people...\n")
    part_3A = part_3[part_3['BLP']==1]
    part_3A['Alive']=1
    part_3A['is_Historical']=0
    part_3B = part_3[part_3['BLP']==0]

    print("Identifying living and historical status based on birth by decades...\n")

    print("collect data with date of birth before 1907...\n")
    birth_from_begin_till_1st_millenium=pd.read_csv(petscan_path / 'birth_from_begin_till_1st_millenium.csv',on_bad_lines='skip', index_col=False)
    birth_2nd_millenium_without_20th_century=pd.read_csv(petscan_path / 'birth_2nd_millenium_without_20th_century.csv',on_bad_lines='skip', index_col=False)
    birth_1900s_without_07_08_09=pd.read_csv(petscan_path / 'birth_1900s_without_07,08,09.csv',on_bad_lines='skip', index_col=False)



    len(birth_from_begin_till_1st_millenium), len(birth_2nd_millenium_without_20th_century)

    print("collect data with date of birth after 1907...\n")
    birth_1907_08_09=pd.read_csv(petscan_path / 'birth_1907,08,09.csv',on_bad_lines='skip', index_col=False)
    birth_20th_century_without_1900s=pd.read_csv(petscan_path / 'birth_20th_century_without_1900s.csv',on_bad_lines='skip', index_col=False)
    birth_21st_century=pd.read_csv(petscan_path / 'birth_21st-century.csv',on_bad_lines='skip', index_col=False)


    historical_people = pd.concat([birth_from_begin_till_1st_millenium,birth_2nd_millenium_without_20th_century,birth_1900s_without_07_08_09])

    contemporary_people = pd.concat([birth_1907_08_09,birth_20th_century_without_1900s,birth_21st_century])

    print("Identifying historical people...\n")
    part_3B_a=part_3B[part_3B['page_title'].isin(historical_people['title'])]
    part_3B_a['Alive']=0
    part_3B_a['is_Historical']=1

    print("Identifying contemporary deceased people...\n")
    part_3B_b=part_3B[~part_3B['page_title'].isin(historical_people['title'])]
    part_3B_b_contemporary=part_3B_b[part_3B_b['page_title'].isin(contemporary_people['title'])]
    dead=pd.read_csv(petscan_path / 'Dead_people_all.csv',on_bad_lines='skip', index_col=False)
    part_3B_b_contemporary_dead=part_3B_b_contemporary[part_3B_b_contemporary['page_title'].isin(dead['title'])]
    part_3B_b_contemporary_dead['Alive']=0
    part_3B_b_contemporary_dead['is_Historical']=0

    print("Identifying data without date of birth and death information...\n")
    Totally_unlnown_group = pd.concat([part_3B_b[~part_3B_b['page_title'].isin(contemporary_people['title'])],part_3B_b_contemporary[~part_3B_b_contemporary['page_title'].isin(dead['title'])]])

    print("Identifying people deceased before 1907...\n")
    dead_historical=pd.read_csv(petscan_path / 'Dead_people_historical.csv',on_bad_lines='skip', index_col=False)
    part_3B_unknown_historical_dead=Totally_unlnown_group[Totally_unlnown_group['page_title'].isin(dead_historical['title'])]
    part_3B_unknown_historical_dead['Alive']=0
    part_3B_unknown_historical_dead['is_Historical']=1


    part_3_better=pd.concat([part_3A,part_3B_a,part_3B_b_contemporary_dead, part_3B_unknown_historical_dead])
    not_part_3=part_3[~part_3['page_title'].isin(part_3_better['page_title'])]

    print("Identifying people deceased after 1907...\n")
    Dead_people_from1900_to1977=pd.read_csv(petscan_path / 'Dead_people_from1900_to1977.csv',on_bad_lines='skip', index_col=False)
    dead_contemporary_2=dead[~dead['title'].isin(pd.concat([dead_historical,Dead_people_from1900_to1977])['title'])]

    print("Consider the rest of people as alive...\n")
    probably_alive=not_part_3[~not_part_3['page_title'].isin(dead_contemporary_2['title'])]
    probably_alive['Alive']=1
    probably_alive['is_Historical']=0

    part_3_better=pd.concat([part_3_better,probably_alive])
    print("Done with Part 3!\n")

    return part_3_better


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

def make_data_for_survival_model(petscan_path,output_path_kmf,output_path_cox_ph):
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
    part_3 = data_part3(part_3,petscan_path)

    print(len(part_1), len(part_2), len(part_3))

    print("Join all the data...\n")
    all_biographies2_with_data=pd.concat([part_1,part_2])
    all_biographies2_with_data.loc[all_biographies2_with_data[all_biographies2_with_data['birth']>=1907].index,'is_Historical']=0
    all_biographies2_with_data.loc[all_biographies2_with_data[all_biographies2_with_data['birth']<1907].index,'is_Historical']=1
    all_biographies2_with_data=pd.concat([all_biographies2_with_data, part_3]).drop_duplicates(subset='page_title', keep='first')

    all_biographies2_with_data=all_biographies2_with_data.rename(columns={'Female':'Gender'})

    print("Identifying the feature Status for all people: a) Historical, b) Contemporary Dead, c) Contemporary Alive...\n")
    all_biographies2_with_data=all_biographies2_with_data.rename(columns={'Female':'Gender'})
    all_biographies2_with_data['Status']=all_biographies2_with_data.apply(lambda row: "Historical" if row['is_Historical']==1 else ("Contemporary Dead" if row['Alive']==0 else "Alive"), axis=1)
    all_biographies2_with_data['Wikipedia_Age']=all_biographies2_with_data['creation_date_original2'].apply(lambda x: int(str(x)[2:4]))
    
    all_biographies2_with_data.to_csv(output_path_cox_ph, index= False)
    print("Done with all_biographies with Vital Information!")



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
    input_path_conv_afd = RAW_DATA_DIR / "From_Begin_Afd_Conversation3.csv",
    output_path_kmf: Path = PROCESSED_DATA_DIR / "all_biographies2.csv",
    output_path_cox_ph: Path = PROCESSED_DATA_DIR / "all_biographies2_with_data.csv",
    output_path_compete: Path = PROCESSED_DATA_DIR / "data_for_compete_risk_all.csv",
    petscan_path: Path = EXTERNAL_DATA_DIR 
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset for Kaplan-Meier estimation...")
    # make_all_biography2(input_path,output_path_kmf)

    logger.info("Processing dataset for Cox proportional hazards model...")
    # make_data_for_survival_model(petscan_path,output_path_kmf,output_path_cox_ph)

    logger.info("Processing dataset for Competeing Risk model...")
    make_data_for_competing_risk_model(input_path_conv_afd,output_path_cox_ph,output_path_compete)
    
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
