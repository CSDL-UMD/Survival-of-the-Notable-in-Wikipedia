from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from dateutil import parser
import datetime

# import tqdm.notebook as nb


from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, EXTERNAL_DATA_DIR, INTERIM_DATA_DIR

import pandas as pd
import re
import os
import warnings

warnings.filterwarnings("ignore")

app = typer.Typer()


def convert(date_time):
    try:
        return datetime.datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.datetime.strptime(str(date_time), "%Y-%m-%d")
    format = "%Y-%m-%d %H:%M:%S"


def prepare_for_r_code(data_for_compete_risk_all, data_for_r_code):
    print("Prepare for R code...\n")
    data_for_compete_risk_all["creation_dates2"] = data_for_compete_risk_all[
        "creation_dates"
    ].apply(lambda x: convert(x))
    data_for_compete_risk_all["nomination_dates2"] = data_for_compete_risk_all[
        "nomination_dates"
    ].apply(lambda x: convert(x))

    print("Data segmentation based on year of creation...\n")
    dataframe_year = pd.DataFrame()
    list_of_pf = []
    iterr = 1
    for year in tqdm(range(2004, 2024, 1)):
        #     print(year)
        create_till = data_for_compete_risk_all[
            data_for_compete_risk_all["creation_dates2"] <= datetime.datetime(year, 12, 31)
        ]

        nominated = create_till[
            create_till["nomination_dates2"] <= datetime.datetime(year, 12, 31)
        ]
        nominated["event2"] = nominated["event"]
        # print(nominated)

        not_nominated = create_till[
            create_till["nomination_dates2"] > datetime.datetime(year, 12, 31)
        ]
        not_nominated["event2"] = "not-nominated"
        conct = pd.concat([nominated, not_nominated])
        conct["iter"] = iterr
        #     print(conct)
        iterr += 1
        list_of_pf.append(conct)

    data_for_compete_risk_all_iter = pd.concat(list_of_pf)

    print("Saving in the interim folder...\n")

    # Check if the folder exists
    if not os.path.exists(data_for_r_code):
        # Create the folder
        os.makedirs(data_for_r_code)
        print(f"Folder created: {data_for_r_code}")
    else:
        print(f"Folder already exists: {data_for_r_code}")

    for i, g in tqdm(data_for_compete_risk_all_iter.groupby("iter")):
        file_name_r = "iter_" + str(i) + ".csv"
        g.to_csv(data_for_r_code / file_name_r, index=False)


def word_count(str):
    counts = dict()
    words = str.split()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return list(counts.values())


def extract_feature_for_competing_risk(afds_all, all_biographies2_with_data):
    print("Extracting features for competing risk analysis...\n")

    groups = afds_all.groupby("page_title")

    features_del = []

    for i, g in tqdm(groups):
        # print(i)

        target = g.sort_values(by="timestamp")
        # print((pd.Timestamp(target.iloc[-1]['timestamp'], unit='s')-pd.Timestamp(all_biographies2_with_data[all_biographies2_with_data['page_title']==i]['nomination_dates'].iloc[0])).total_seconds())

        num_users = num_messages = num_words = num_seconds = 0
        try:
            if len(target) > 0:
                num_users = len(target["user"].unique()) + 1
                num_messages = len(target) + 1
                ave_num_words = (
                    sum(target["rationals"].apply(lambda x: word_count(str(x))).sum())
                    / (num_messages - 1)
                ) + 1
                num_seconds = (
                    pd.Timestamp(target.iloc[-1]["timestamp"], unit="s")
                    - pd.Timestamp(target.iloc[0]["timestamp"], unit="s")
                ).total_seconds()

                if num_seconds == 0:
                    # print(i[0])
                    # print(all_biographies2_with_data[all_biographies2_with_data['page_title']==i])
                    num_seconds = (
                        pd.Timestamp(target.iloc[-1]["timestamp"], unit="s")
                        - pd.Timestamp(
                            all_biographies2_with_data[
                                all_biographies2_with_data["page_title"] == i
                            ]["nomination_dates"].iloc[0]
                        )
                    ).total_seconds()

            features_del.append([i, num_seconds, num_users, num_messages, ave_num_words])
        except:
            pass

    df_features_del = pd.DataFrame(
        features_del,
        columns=["page_title", "num_seconds", "num_users", "num_messages", "ave_num_words"],
    )
    df_features_del = df_features_del[df_features_del["num_seconds"] > 0]
    return df_features_del


def parse_and_clean_outcomes(all_biographies2_with_data, df_features_del, afds_all):
    print("Organizing all data for competing risk analysis...\n")
    data_for_compete_risk = all_biographies2_with_data[
        [
            "QID",
            "page_title",
            "creation_dates",
            "nomination_dates",
            "days_before_nomination",
            "nominated",
            "Gender",
            "Wikipedia_Age",
            "Status",
        ]
    ]
    data_for_compete_risk["tstart"] = 0
    data_for_compete_risk["tstop"] = data_for_compete_risk["days_before_nomination"] * 86400
    data_for_compete_risk["event"] = data_for_compete_risk["nominated"].apply(
        lambda x: "not nominated" if x == 0 else "nominated"
    )
    data_for_compete_risk["id"] = data_for_compete_risk.index
    data_for_compete_risk = data_for_compete_risk.drop_duplicates(subset="id", keep="first")

    print("Organizing data of nominated afd for competing risk analysis...\n")
    data_for_compete_risk_nominated = pd.merge(
        data_for_compete_risk,
        df_features_del,
        on="page_title",
    )[
        [
            "QID",
            "page_title",
            "creation_dates",
            "nomination_dates",
            "days_before_nomination",
            "nominated",
            "Gender",
            "Wikipedia_Age",
            "Status",
            "id",
            "num_seconds",
            "num_users",
            "num_messages",
            "ave_num_words",
        ]
    ]
    data_for_compete_risk_nominated = data_for_compete_risk_nominated.drop_duplicates(
        subset="id", keep="first"
    )
    data_for_compete_risk_nominated["tstart"] = (
        data_for_compete_risk_nominated["days_before_nomination"] * 86400
    )
    data_for_compete_risk_nominated["tstop"] = (
        data_for_compete_risk_nominated["tstart"] + data_for_compete_risk_nominated["num_seconds"]
    )
    data_for_compete_risk_nominated = pd.merge(
        data_for_compete_risk_nominated,
        afds_all[afds_all["action"] == "Outcome"][["page_title", "recommend"]],
        on="page_title",
        how="left",
    ).drop_duplicates(subset="id", keep="first")
    data_for_compete_risk_nominated = data_for_compete_risk_nominated.rename(
        columns={"recommend": "event"}
    )
    data_for_compete_risk_nominated = data_for_compete_risk_nominated.drop(columns="num_seconds")

    print("Cleaning the text of outcome...\n")

    data_for_compete_risk_nominated["event2"] = (
        data_for_compete_risk_nominated["event"]
        .apply(
            lambda x: str(x)
            .lower()
            .replace("not delete", "keep")
            .replace("delete and redirect", "redirect")
            .replace("kept", "keep")
        )
        .apply(
            lambda x: (
                re.search(
                    r"delete|deletion|keep|no consensus|redirect|merge|withdraw|close|speedied|moot|a7|move|inclusion",
                    x,
                ).group(0)
                if bool(
                    re.search(
                        r"delete|deletion|keep|no consensus|redirect|merge|withdraw|close|speedied|moot|a7|move|inclusion",
                        x,
                    )
                )
                == True
                else x
            )
        )
        .apply(
            lambda x: x.replace('<span style="color:red;">', "")
            .replace("</span>", "")
            .replace("<font color=green>", "")
            .replace("</font>", "")
            .replace("<font color=red>", "")
            .replace("withdraw", "keep")
            .replace("kept", "keep")
        )
    )
    data_for_compete_risk_nominated["event2"] = data_for_compete_risk_nominated["event2"].apply(
        lambda x: x.replace("copyvio", "delete")
        .replace("speedied", "delete")
        .replace("speedy", "delete")
        .replace("deletion", "delete")
        .replace("a7", "delete")
        .replace("flagged as ", "")
        .replace("move", "keep")
        .replace("close", "keep")
        .replace("no concensus", "no consensus")
        .replace("no consensus", "keep")
        .replace("moot", "keep")
        .replace("inclusion", "keep")
        .replace("procedural closure", "keep")
        .replace("userfy", "keep")
        .replace("userfied", "keep")
    )

    data_for_compete_risk_nominated = data_for_compete_risk_nominated.drop(columns="event").rename(
        columns={"event2": "event"}
    )

    print("Organizing most frequent event/outcome...\n")
    data_for_compete_risk["num_users"] = 0
    data_for_compete_risk["num_messages"] = 0
    data_for_compete_risk["ave_num_words"] = 0

    data_for_compete_risk_all = pd.concat(
        [
            data_for_compete_risk_nominated,
            data_for_compete_risk[data_for_compete_risk_nominated.columns],
        ]
    ).fillna(0)
    list_cat = list(data_for_compete_risk_all["event"].value_counts()[:6].index)
    data_for_compete_risk_all["event"] = data_for_compete_risk_all["event"].apply(
        lambda x: x if x in list_cat else "other"
    )
    data_for_compete_risk_all["event"] = data_for_compete_risk_all["event"].apply(
        lambda x: x.replace(" ", "-")
    )
    data_for_compete_risk_all = data_for_compete_risk_all.sort_values(by="id")
    data_for_compete_risk_all = data_for_compete_risk_all[
        data_for_compete_risk_all["tstop"] != data_for_compete_risk_all["tstart"]
    ]
    data_for_compete_risk_all = data_for_compete_risk_all[
        data_for_compete_risk_all["tstop"] <= 8395 * 86400
    ].sort_values(by="tstop")

    return data_for_compete_risk_all


def make_data_for_competing_risk_model(
    input_path_conv_afd, output_path_cox_ph, output_path_compete, data_for_r_code
):
    articles = pd.read_csv(input_path_conv_afd, index_col=False)
    print("Extracting the outcome from the conversation...\n")
    articles["page_title"] = articles["Entry"].apply(lambda x: str(x).replace(" ", "_"))

    all_biographies2_with_data = pd.read_csv(output_path_cox_ph, index_col=False)
    afds = pd.merge(
        articles[articles["action"] == "Outcome"][["page_title", "recommend"]],
        all_biographies2_with_data,
        on="page_title",
    ).drop_duplicates(subset="page_title")
    afds["outcome"] = afds["recommend"].apply(
        lambda y: str(
            re.findall(
                "delete|keep|merge|redirect|no consensus|d</span>elete|withdrawn|deletion|close|inclusion",
                str(y).lower(),
                flags=re.IGNORECASE,
            )
        )
        .replace("'", "")
        .replace("[", "")
        .replace("]", "")
    )

    afds_all = pd.merge(
        afds[["page_title", "outcome"]], articles[articles["timestamp"] != -1], on="page_title"
    )
    afds_all["recommend"] = afds_all["recommend"].apply(lambda x: str(x).lower())
    df_features_del = extract_feature_for_competing_risk(afds_all, all_biographies2_with_data)
    data_for_compete_risk_all = parse_and_clean_outcomes(
        all_biographies2_with_data, df_features_del, afds_all
    )

    data_for_compete_risk_all.to_csv(output_path_compete, index=False)

    prepare_for_r_code(data_for_compete_risk_all, data_for_r_code)


def data_part3(part_3, petscan_path):
    print("Identifying living people...\n")
    part_3A = part_3[part_3["BLP"] == 1]
    part_3A["Alive"] = 1
    part_3A["is_Historical"] = 0
    part_3B = part_3[part_3["BLP"] == 0]

    print("Identifying living and historical status based on birth by decades...\n")

    print("collect data with date of birth before 1907...\n")
    birth_from_begin_till_1st_millenium = pd.read_csv(
        petscan_path / "birth_from_begin_till_1st_millenium.csv",
        on_bad_lines="skip",
        index_col=False,
    )
    birth_2nd_millenium_without_20th_century = pd.read_csv(
        petscan_path / "birth_2nd_millenium_without_20th_century.csv",
        on_bad_lines="skip",
        index_col=False,
    )
    birth_1900s_without_07_08_09 = pd.read_csv(
        petscan_path / "birth_1900s_without_07,08,09.csv", on_bad_lines="skip", index_col=False
    )

    len(birth_from_begin_till_1st_millenium), len(birth_2nd_millenium_without_20th_century)

    print("collect data with date of birth after 1907...\n")
    birth_1907_08_09 = pd.read_csv(
        petscan_path / "birth_1907,08,09.csv", on_bad_lines="skip", index_col=False
    )
    birth_20th_century_without_1900s = pd.read_csv(
        petscan_path / "birth_20th_century_without_1900s.csv", on_bad_lines="skip", index_col=False
    )
    birth_21st_century = pd.read_csv(
        petscan_path / "birth_21st-century.csv", on_bad_lines="skip", index_col=False
    )

    historical_people = pd.concat(
        [
            birth_from_begin_till_1st_millenium,
            birth_2nd_millenium_without_20th_century,
            birth_1900s_without_07_08_09,
        ]
    )

    contemporary_people = pd.concat(
        [birth_1907_08_09, birth_20th_century_without_1900s, birth_21st_century]
    )

    print("Identifying historical people...\n")
    part_3B_a = part_3B[part_3B["page_title"].isin(historical_people["title"])]
    part_3B_a["Alive"] = 0
    part_3B_a["is_Historical"] = 1

    print("Identifying contemporary deceased people...\n")
    part_3B_b = part_3B[~part_3B["page_title"].isin(historical_people["title"])]
    part_3B_b_contemporary = part_3B_b[part_3B_b["page_title"].isin(contemporary_people["title"])]
    dead = pd.read_csv(petscan_path / "Dead_people_all.csv", on_bad_lines="skip", index_col=False)
    part_3B_b_contemporary_dead = part_3B_b_contemporary[
        part_3B_b_contemporary["page_title"].isin(dead["title"])
    ]
    part_3B_b_contemporary_dead["Alive"] = 0
    part_3B_b_contemporary_dead["is_Historical"] = 0

    print("Identifying data without date of birth and death information...\n")
    Totally_unlnown_group = pd.concat(
        [
            part_3B_b[~part_3B_b["page_title"].isin(contemporary_people["title"])],
            part_3B_b_contemporary[~part_3B_b_contemporary["page_title"].isin(dead["title"])],
        ]
    )

    print("Identifying people deceased before 1907...\n")
    dead_historical = pd.read_csv(
        petscan_path / "Dead_people_historical.csv", on_bad_lines="skip", index_col=False
    )
    part_3B_unknown_historical_dead = Totally_unlnown_group[
        Totally_unlnown_group["page_title"].isin(dead_historical["title"])
    ]
    part_3B_unknown_historical_dead["Alive"] = 0
    part_3B_unknown_historical_dead["is_Historical"] = 1

    part_3_better = pd.concat(
        [part_3A, part_3B_a, part_3B_b_contemporary_dead, part_3B_unknown_historical_dead]
    )
    not_part_3 = part_3[~part_3["page_title"].isin(part_3_better["page_title"])]

    print("Identifying people deceased after 1907...\n")
    Dead_people_from1900_to1977 = pd.read_csv(
        petscan_path / "Dead_people_from1900_to1977.csv", on_bad_lines="skip", index_col=False
    )
    dead_contemporary_2 = dead[
        ~dead["title"].isin(pd.concat([dead_historical, Dead_people_from1900_to1977])["title"])
    ]

    print("Consider the rest of people as alive...\n")
    probably_alive = not_part_3[~not_part_3["page_title"].isin(dead_contemporary_2["title"])]
    probably_alive["Alive"] = 1
    probably_alive["is_Historical"] = 0

    part_3_better = pd.concat([part_3_better, probably_alive])
    print("Done with Part 3!\n")

    return part_3_better


def data_part2(part_2, petscan_path):
    logger.info(
        "Part 2: Set up and correct the data, ensuring entries with a birth date but no death date are properly handled...\n"
    )
    print("Removing data with wrong date of birth...\n")
    part_2["wrong"] = part_2.apply(
        lambda row: 1 if int(str(row["creation_date_original2"])[:4]) < row["birth"] else 0, axis=1
    )
    part_2 = part_2[part_2["wrong"] == 0]
    part_2 = part_2.drop(columns=["wrong"])

    print("Identifying people born before 1907...\n")
    part_2C = part_2[part_2["birth"] < 1907]
    part_2C["Alive"] = 0

    print("Identifying people born after 1907 and alive...\n")
    part_2_notC = part_2[part_2["birth"] >= 1907]
    part_2A = part_2_notC[part_2_notC["BLP"] == 1]
    part_2A["Alive"] = 1

    print("Identifying people born after 1907 and deceased...\n")
    part_2B = part_2_notC[part_2_notC["BLP"] == 0]
    dead = pd.read_csv(petscan_path / "Dead_people_all.csv", on_bad_lines="skip", index_col=False)
    part_2B_a = part_2B[part_2B["page_title"].isin(dead["title"])].drop_duplicates(
        subset="page_title", keep="first"
    )
    part_2B_a["Alive"] = 0
    part_2B_b = part_2B[~part_2B["page_title"].isin(dead["title"])].drop_duplicates(
        subset="page_title", keep="first"
    )
    part_2B_b["Alive"] = 1

    part_2 = pd.concat([part_2A, part_2B_a, part_2B_b, part_2C])
    print("Done with Part 2!\n")
    return part_2


def data_part1(part_1):
    logger.info(
        "Part 1: Set up and process the data, focusing on entries that include a recorded date of death....\n"
    )
    part_1["Alive"] = 0

    print("Splitting data based on availbility of date of birth...\n")
    part_1A = part_1[part_1["birth"] != "no data"]
    part_1B = part_1[part_1["birth"] == "no data"]

    print("Removing data with wrong date of birth...\n")
    part_1A["wrong"] = part_1A.apply(
        lambda row: 1 if int(str(row["creation_date_original2"])[:4]) < row["birth"] else 0, axis=1
    )
    part_1A = part_1A[part_1A["wrong"] == 0]
    part_1A = part_1A.drop(columns=["wrong"])

    print("Identifying date of birth of the people who are dead...\n")
    part_1B["birth"] = part_1B["death"].apply(lambda x: x - 70)

    part_1 = pd.concat([part_1A, part_1B])

    print(
        "Identifying the living people at the time of nomination who are deceased after 2000...\n"
    )
    part_1_after2000 = part_1[part_1["death"] >= 2000]
    part_1_before2000 = part_1[part_1["death"] < 2000]
    part_1_after2000["Alive"] = part_1_after2000.apply(
        lambda row: (
            1
            if pd.to_datetime(row["nomination_dates"], utc=True)
            < pd.to_datetime(str(row["death"]).replace("+", ""), utc=True)
            else 0
        ),
        axis=1,
    )

    part_1 = pd.concat([part_1_before2000, part_1_after2000])
    print("Done with Part 1!")

    return part_1


def make_data_for_survival_model(petscan_path, output_path_kmf, output_path_cox_ph):
    print("Loading list of Living People...\n")
    BLP = pd.read_csv(petscan_path / "Living_people.csv", index_col=False)
    BLP = BLP[["title"]]
    all_biographies2 = pd.read_csv(output_path_kmf, index_col=False)

    print("Merging All biographies with Living people...\n")
    all_biographies2_BLP = pd.merge(
        all_biographies2, BLP, left_on="page_title", right_on="title", how="left"
    )
    all_biographies2_BLP["BLP"] = all_biographies2_BLP["title"].fillna(0)
    all_biographies2_BLP["Entry2"] = all_biographies2_BLP["Entry"].apply(
        lambda x: x.replace(" ", "_")
    )
    all_biographies2_BLP.loc[
        all_biographies2_BLP[
            (all_biographies2_BLP["Entry2"].isin(BLP["title"]))
            & (all_biographies2_BLP["BLP"] == 0)
        ].index,
        "BLP",
    ] = 1
    all_biographies2_BLP.loc[all_biographies2_BLP["BLP"] != 0, "BLP"] = 1

    print("Recoding Gender covariate...\n")
    all_biographies2_BLP.loc[all_biographies2_BLP["gender"] == "female", "Female"] = 1
    all_biographies2_BLP.loc[all_biographies2_BLP["gender"] != "female", "Female"] = 0

    print("Formating date of birth and death...\n")
    all_biographies2_BLP["birth"] = all_biographies2_BLP["date_of_birth"].apply(
        lambda x: (
            -1 * int(x.split("-")[1])
            if x[0] == "-"
            else (
                int(x.split("-")[0])
                if len(x.split("-")[0]) == 4
                else (int(x.split("-")[0]) if x[0] == "+" else "no data")
            )
        )
    )
    all_biographies2_BLP["death"] = all_biographies2_BLP["date_of_death"].apply(
        lambda x: (
            -1 * int(x.split("-")[1])
            if x[0] == "-"
            else (
                int(x.split("-")[0])
                if len(x.split("-")[0]) == 4
                else (int(x.split("-")[0]) if x[0] == "+" else "no data")
            )
        )
    )

    print("Splitting dataset based on the availability of dates of birth and death\n")
    part_1 = all_biographies2_BLP[all_biographies2_BLP["death"] != "no data"]
    part_2 = all_biographies2_BLP[
        (all_biographies2_BLP["birth"] != "no data") & (all_biographies2_BLP["death"] == "no data")
    ]
    part_3 = all_biographies2_BLP[
        (all_biographies2_BLP["birth"] == "no data") & (all_biographies2_BLP["death"] == "no data")
    ]
    print("Data is splitted in 3 parts!\n")

    part_1 = data_part1(part_1)
    part_2 = data_part2(part_2, petscan_path)
    part_3 = data_part3(part_3, petscan_path)

    print(len(part_1), len(part_2), len(part_3))

    print("Join all the data...\n")
    all_biographies2_with_data = pd.concat([part_1, part_2])
    all_biographies2_with_data.loc[
        all_biographies2_with_data[all_biographies2_with_data["birth"] >= 1907].index,
        "is_Historical",
    ] = 0
    all_biographies2_with_data.loc[
        all_biographies2_with_data[all_biographies2_with_data["birth"] < 1907].index,
        "is_Historical",
    ] = 1
    all_biographies2_with_data = pd.concat([all_biographies2_with_data, part_3]).drop_duplicates(
        subset="page_title", keep="first"
    )

    all_biographies2_with_data = all_biographies2_with_data.rename(columns={"Female": "Gender"})

    print(
        "Identifying the feature Status for all people: a) Historical, b) Contemporary Dead, c) Contemporary Alive...\n"
    )
    all_biographies2_with_data = all_biographies2_with_data.rename(columns={"Female": "Gender"})
    all_biographies2_with_data["Status"] = all_biographies2_with_data.apply(
        lambda row: (
            "Historical"
            if row["is_Historical"] == 1
            else ("Contemporary Dead" if row["Alive"] == 0 else "Alive")
        ),
        axis=1,
    )
    all_biographies2_with_data["Wikipedia_Age"] = all_biographies2_with_data[
        "creation_date_original2"
    ].apply(lambda x: int(str(x)[2:4]))

    all_biographies2_with_data.to_csv(output_path_cox_ph, index=False)
    print("Done with all_biographies with Vital Information!")


def make_all_biography2(all_biographies, output_path_kmf):

    logger.info(
        "Preparation involves filtering the data as follows: a) Retain entries where the creation dates precede the nomination dates. b) Include only data pertaining to subjects identified as male or female."
    )
    all_biographies = all_biographies[all_biographies["gender"] != "no data"]

    print("Counting days before nomination...\n")
    all_biographies["days_before_nomination"] = (
        (
            all_biographies["rev_timestamp"]
            .apply(str)
            .apply(
                lambda x: pd.Timestamp(
                    int(x[:4]),
                    int(x[4:6]),
                    int(x[6:8]),
                    int(x[8:10]),
                    int(x[10:12]),
                    int(x[12:14]),
                )
            )
            - all_biographies["creation_date_original2"]
            .apply(str)
            .apply(
                lambda x: pd.Timestamp(
                    int(x[:4]),
                    int(x[4:6]),
                    int(x[6:8]),
                    int(x[8:10]),
                    int(x[10:12]),
                    int(x[12:14]),
                )
            )
        )
        .apply(lambda x: x.total_seconds())
        .apply(lambda x: x / 86400)
    )

    print("Formating creation dates...\n")
    all_biographies["creation_dates"] = (
        all_biographies["creation_date_original2"]
        .apply(str)
        .apply(
            lambda x: pd.Timestamp(
                int(x[:4]), int(x[4:6]), int(x[6:8]), int(x[8:10]), int(x[10:12]), int(x[12:14])
            )
        )
    )

    print("Formating nomination dates...\n")
    all_biographies["nomination_dates"] = (
        all_biographies["rev_timestamp"]
        .apply(str)
        .apply(
            lambda x: pd.Timestamp(
                int(x[:4]), int(x[4:6]), int(x[6:8]), int(x[8:10]), int(x[10:12]), int(x[12:14])
            )
        )
    )

    all_biographies2 = all_biographies[(all_biographies["days_before_nomination"] >= 0)]
    all_biographies2 = all_biographies2[all_biographies2["gender"].isin(["male", "female"])]

    all_biographies2.to_csv(output_path_kmf, index=False)
    print("Done with all_biographies2!")


# --This Section is for combining all information: a) Biographies, b) creation dates, c) nomination dates, d) vital information ----


# get creation date either from PAGE table or ARCHIVE table
def get_creation(df, creation, archive_unique):
    creation_part = (
        pd.merge(df, creation, on="page_title", how="left")
        .drop_duplicates(subset="page_title")
        .fillna("no data")
    )

    first = creation_part[creation_part["creation_date_original"] != "no data"][
        ["page_title", "creation_date_original"]
    ]

    archive_part = pd.merge(
        df, archive_unique, left_on="page_title", right_on="ar_title", how="left"
    ).fillna("no data")

    second = archive_part[archive_part["ar_timestamp"] != "no data"][
        ["page_title", "ar_timestamp"]
    ]

    first_second = pd.merge(first, second, on="page_title", how="outer", indicator=True)

    first_second_both = first_second[first_second["_merge"] == "both"][
        ["page_title", "creation_date_original", "ar_timestamp"]
    ]

    first_second_both["creation_date_original2"] = first_second_both.apply(
        lambda row: (
            int(row["creation_date_original"])
            if int(row["creation_date_original"]) <= int(row["ar_timestamp"])
            else int(row["ar_timestamp"])
        ),
        axis=1,
    )

    first_second_either = first_second[first_second["_merge"] != "both"]

    first_second_either["creation_date_original2"] = first_second_either.apply(
        lambda row: (
            int(row["creation_date_original"])
            if row["_merge"] == "left_only"
            else int(row["ar_timestamp"])
        ),
        axis=1,
    )

    return pd.concat(
        [
            first_second_both[["page_title", "creation_date_original2"]],
            first_second_either[["page_title", "creation_date_original2"]],
        ]
    ).drop_duplicates(subset="page_title")


# Load Biographies with creation dates from PAGE table.
# Load creation dates from Archive table
# Merge these two datasets
def add_creation_dates(input_path_quarry):
    print("Loading Bio-Set...\n")
    creation = pd.read_csv(
        input_path_quarry / "Wikiproject_Bio2_creation_dates.csv", index_col=False
    )
    creation.columns = ["page_id", "page_title", "Entry", "creation_timestamp"]

    creation["creation_timestamp2"] = creation["creation_timestamp"].apply(
        lambda x: (
            int(
                str(x).split("T")[0].replace("-", "")
                + str(x).split("T")[1].replace(":", "").replace("Z", "")
            )
            if x != "no data"
            else 20231110080000
        )
    )

    print("Loading Archive set...\n")
    archive = pd.read_csv(input_path_quarry / "Archive_all_8_Nov.csv", index_col=False)

    archive_unique = archive.sort_values("ar_timestamp").drop_duplicates(
        subset="ar_title", keep="first"
    )

    creation_archive_merged = pd.merge(
        creation, archive_unique, left_on="page_title", right_on="ar_title", how="left"
    )

    creation_archive_merged2 = creation_archive_merged[
        ["page_id", "page_title", "Entry", "creation_timestamp2", "ar_timestamp"]
    ]

    # add a random date as place holder
    creation_archive_merged2["ar_timestamp2"] = creation_archive_merged2["ar_timestamp"].fillna(
        20231110080000
    )

    creation_archive_merged2["creation_date_original"] = creation_archive_merged2.apply(
        lambda row: (
            int(row["creation_timestamp2"])
            if row["creation_timestamp2"] < row["ar_timestamp2"]
            else int(row["ar_timestamp2"])
        ),
        axis=1,
    )

    creation_archive_merged2 = creation_archive_merged2[
        ["page_id", "page_title", "Entry", "creation_date_original"]
    ]

    return creation_archive_merged2


# Correct data where the creation date is after the nomination date
def correct_create_date(wikidata_page_id_nominated_create, creation, archive_unique):
    print("Correct data where the creation date is after the nomination date")
    larger_create_date = wikidata_page_id_nominated_create[
        wikidata_page_id_nominated_create["creation_date_original2"]
        > wikidata_page_id_nominated_create["rev_timestamp"]
    ]

    larger_create_date2 = get_creation(
        larger_create_date[["page_title"]], creation, archive_unique
    )

    larger_create_date_merged = pd.merge(larger_create_date2, larger_create_date, on="page_title")

    extract_original_date = larger_create_date_merged[
        larger_create_date_merged["creation_date_original2_x"]
        < larger_create_date_merged["rev_timestamp"]
    ][["page_title", "creation_date_original2_x"]]

    extract_original_date2 = pd.merge(
        extract_original_date, wikidata_page_id_nominated_create, on="page_title"
    ).drop(columns="creation_date_original2")

    extract_original_date2 = extract_original_date2.rename(
        columns={"creation_date_original2_x": "creation_date_original2"}
    )

    wikidata_page_id_nominated_create2 = pd.concat(
        [
            wikidata_page_id_nominated_create[
                ~wikidata_page_id_nominated_create["page_title"].isin(
                    extract_original_date2["page_title"]
                )
            ],
            extract_original_date2,
        ]
    )

    return wikidata_page_id_nominated_create2


# Extract creation dates of nominated arctices
def extract_data_of_nominated_articles(
    wikidata_page_id_nominated2, wikidata_page_id_all, creation, archive_unique
):
    print("Handling nominated articles first...\n")
    focus_wikidata_page_id_nominated2 = wikidata_page_id_nominated2[
        ["page_title", "QID", "rev_timestamp"]
    ]
    focus_wikidata_page_id_all = wikidata_page_id_all[["page_title", "QID"]]

    focus_group = pd.merge(
        focus_wikidata_page_id_nominated2, focus_wikidata_page_id_all, on="QID"
    ).drop_duplicates(subset="QID")
    focus_group = focus_group.rename(columns={"page_title_y": "page_title"})

    print("Get creation dates of nominated articles which are still available...\n")
    data = get_creation(focus_group, creation, archive_unique)
    data1 = pd.merge(focus_group, data, on="page_title")[
        ["page_title_x", "creation_date_original2", "rev_timestamp", "QID"]
    ]

    data_part1 = pd.merge(data1, wikidata_page_id_all, on="QID").drop_duplicates(
        subset="page_title_x"
    )
    data_part1 = data_part1.drop(columns=["page_title"]).rename(
        columns={"page_title_x": "page_title"}
    )

    print("Get creation dates of nominated articles which are not available...\n")
    rest_data = wikidata_page_id_nominated2[
        ~wikidata_page_id_nominated2["page_title"].isin(data_part1["page_title"])
    ]
    rest_data2 = get_creation(rest_data, creation, archive_unique)
    data_part2 = pd.merge(rest_data2, rest_data, on="page_title")

    wikidata_page_id_nominated_create = pd.concat(
        [data_part1[list(data_part2.columns)], data_part2]
    ).drop_duplicates(subset="page_title")

    wikidata_page_id_nominated_create_final = correct_create_date(
        wikidata_page_id_nominated_create, creation, archive_unique
    )

    return wikidata_page_id_nominated_create_final


# combine all data
def join_creation_dates_vital_info_nomination_date(
    input_path_quarry, input_path_wikidata, input_path_conv_afd
):
    creation = add_creation_dates(input_path_quarry)
    print(creation.head())

    print("Loading Q5 set with vital information...\n")
    wikidata_page_id_all = pd.read_csv(
        input_path_wikidata / "wikidata_page_id_all2_merged.csv", index_col=False
    )
    wikidata_page_id_nominated = pd.read_csv(
        input_path_wikidata / "Wikidata_Gender_Birth_Death_nominated.csv", index_col=False
    )

    nomination = pd.read_csv(input_path_quarry / "All_AfDs_3_Nov_2.csv", index_col=False)
    nomination = nomination.rename(columns={"Entry": "page_title"})

    archive = pd.read_csv(input_path_quarry / "Archive_all_8_Nov.csv", index_col=False)
    archive_unique = archive.sort_values("ar_timestamp").drop_duplicates(
        subset="ar_title", keep="first"
    )

    wikidata_page_id_all = wikidata_page_id_all.drop(columns="page_id")
    creation = creation.sort_values("creation_date_original")

    wikidata_page_id_nominated = wikidata_page_id_nominated[
        wikidata_page_id_nominated["instance of"] == "human"
    ]
    wikidata_page_id_nominated = wikidata_page_id_nominated.drop(columns="instance of")
    wikidata_page_id_nominated = wikidata_page_id_nominated[list(wikidata_page_id_all.columns)]
    wikidata_page_id_nominated = wikidata_page_id_nominated.drop_duplicates(
        subset="page_title", keep="last"
    )
    wikidata_page_id_nominated2 = pd.merge(
        nomination, wikidata_page_id_nominated, on="page_title"
    ).drop_duplicates(subset="page_title")

    wikidata_page_id_nominated_create_final = extract_data_of_nominated_articles(
        wikidata_page_id_nominated2, wikidata_page_id_all, creation, archive_unique
    )

    print("Handling not nominated articles now...\n")
    wikidata_page_id_all_not_nominated = wikidata_page_id_all[
        ~wikidata_page_id_all["QID"].isin(wikidata_page_id_nominated_create_final["QID"])
    ]
    data3 = get_creation(wikidata_page_id_all_not_nominated, creation, archive_unique)
    # setting invalid nomination date for non nominated
    data3["rev_timestamp"] = 20231104000000

    wikidata_page_id_all_not_nominated2 = pd.merge(
        data3, wikidata_page_id_all_not_nominated, on="page_title"
    ).drop_duplicates(subset="page_title")
    wikidata_page_id_all_not_nominated_create_final = wikidata_page_id_all_not_nominated2[
        ~wikidata_page_id_all_not_nominated2["page_title"].isin(
            wikidata_page_id_nominated_create_final["page_title"]
        )
    ]

    wikidata_page_id_all_not_nominated_create_final["nominated"] = 0
    wikidata_page_id_nominated_create_final["nominated"] = 1

    all_biographies = pd.concat(
        [wikidata_page_id_nominated_create_final, wikidata_page_id_all_not_nominated_create_final]
    ).drop_duplicates(subset="page_title", keep="first")

    print("Fixing nominated data that have records in the AfD conversation log dataset...\n")
    articles = pd.read_csv(input_path_conv_afd, index_col=False)
    articles["page_title"] = articles["Entry"].apply(lambda x: str(x).replace(" ", "_"))
    afds = pd.merge(
        articles[articles["action"] == "Nomination"][["page_title", "date", "timestamp"]],
        all_biographies,
        on="page_title",
    ).drop_duplicates(subset="page_title")

    afds_need_nomination = afds[afds["nominated"] == 0].sort_values("timestamp")
    afds_need_nomination["rev_timestamp"] = (
        afds_need_nomination["timestamp"]
        .apply(lambda x: pd.Timestamp(x, unit="s"))
        .apply(
            lambda x1: int(
                str(x1).split(" ")[0].replace("-", "") + str(x1).split(" ")[1].replace(":", "")
            )
        )
    )
    afds_need_nomination["nominated"] = 1

    all_biographies2 = pd.concat(
        [
            afds_need_nomination[all_biographies.columns],
            all_biographies[
                ~all_biographies["page_title"].isin(afds_need_nomination["page_title"])
            ],
        ]
    ).drop_duplicates(subset="page_title", keep="first")

    print("Handling data that were nominated multiple times...\n")
    nomination["other_nomination"] = nomination["page_title"].apply(
        lambda x: str(x).split("_(")[0] if "nomination" in str(x) else "no data"
    )
    temp = pd.merge(
        nomination[nomination["other_nomination"] != "no data"],
        all_biographies,
        left_on="other_nomination",
        right_on="page_title",
    )
    more_nomination = (
        temp[(temp["rev_timestamp_x"] >= temp["creation_date_original2"])]
        .sort_values("rev_timestamp_x")
        .drop_duplicates(subset="other_nomination")
    )
    more_nomination = more_nomination.drop(
        columns=["page_title_x", "rev_timestamp_y", "other_nomination"]
    )
    more_nomination = more_nomination.rename(
        columns={"page_title_y": "page_title", "rev_timestamp_x": "rev_timestamp"}
    )[all_biographies.columns]
    more_nomination["nominated"] = 1
    all_biographies2 = pd.concat(
        [
            more_nomination,
            all_biographies2[~all_biographies2["page_title"].isin(more_nomination["page_title"])],
        ]
    )

    return all_biographies2


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path_quarry: Path = RAW_DATA_DIR / "Quarry",
    input_path_wikidata: Path = RAW_DATA_DIR / "Wikidata",
    input_path_conv_afd=RAW_DATA_DIR / "From_Begin_Afd_Conversation3.csv",
    output_path_kmf: Path = PROCESSED_DATA_DIR / "all_biographies2.csv",
    output_path_cox_ph: Path = PROCESSED_DATA_DIR / "all_biographies2_with_data.csv",
    output_path_compete: Path = PROCESSED_DATA_DIR / "data_for_compete_risk_all.csv",
    petscan_path: Path = EXTERNAL_DATA_DIR,
    data_for_r_code: Path = INTERIM_DATA_DIR,
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    logger.info("Join Biographies with creation dates, nomination  dates and Vital information...")
    all_biographies = join_creation_dates_vital_info_nomination_date(
        input_path_quarry, input_path_wikidata, input_path_conv_afd
    )

    logger.info("Processing dataset for Kaplan-Meier estimation...")
    make_all_biography2(all_biographies, output_path_kmf)

    logger.info("Processing dataset for Cox proportional hazards model...")
    make_data_for_survival_model(petscan_path, output_path_kmf, output_path_cox_ph)

    logger.info("Processing dataset for Competeing Risk model...")
    make_data_for_competing_risk_model(
        input_path_conv_afd, output_path_cox_ph, output_path_compete, data_for_r_code
    )

    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
