import pandas as pd
import requests
# from datetime import datetime
from functools import partial
import sys
import re

pd.options.mode.copy_on_write = True

def unit_name_convert(in_str):
    if in_str == "0_VS":
        return "vs"
    elif in_str == "1_L/n":
        return "l/n"
    elif in_str == "2_MMJ":
        return "mmj"
    elif in_str == "3_VBS":
        return "vbs"
    elif in_str == "4_WxS":
        return "wxs"
    elif in_str == "5_25":
        return "n25"
    elif in_str == "混合":
        return "mix"
    else:
        print("unrecognized event type", in_str)
        sys.exit(1)

def make_date_str(in_str, hour):
    datetime_str = in_str.split("*")[0].strip()
    return pd.to_datetime(datetime_str + f"T{hour}",  format="%Y/%m/%dT%H")

def read_date_str(in_str):
    weekday_start_idx = re.search(r"\(|（", in_str).start()
    weekday_end_idx = re.search(r"\)|）", in_str).start()
    datetime_str = in_str[:weekday_start_idx] + in_str[weekday_end_idx+1:]
    
    return pd.to_datetime(datetime_str, format="%Y/%m/%d %H時%M分")

def date_convert(in_df, start=False, end=False):
    # res_sr = pd.Series(index = in_df.index)
    
    make_date_str_T20 = partial(make_date_str, hour=20)
    make_date_str_T15 = partial(make_date_str, hour=15)
    make_date_str_T21 = partial(make_date_str, hour=21)
    
    if start:
        res_sr = in_df["開始日"]
        
        # [special attend] World Link starts and ends at different time
        world_link_sr = in_df["形式"] == "ワールドリンク"
        res_sr[world_link_sr] = in_df[world_link_sr]["開始日"].apply(make_date_str_T20)
        
        # [special attend] one event started with delay due to extended maintenance
        res_sr[120] = pd.Timestamp(2024, 1, 31, 20)
        res_sr[145] = pd.Timestamp(2024, 10, 12, 18)
        
        # normal event start time
        remains_sr = res_sr.apply(lambda x: type(x) == str)
        res_sr[remains_sr] = in_df[remains_sr]["開始日"].apply(make_date_str_T15)
    
    elif end:
        res_sr = in_df["終了日"]
        
        # [special attend] World Link starts and ends at different time
        world_link_sr = in_df["形式"] == "ワールドリンク"
        res_sr[world_link_sr] = in_df[world_link_sr]["終了日"].apply(make_date_str_T20)
        
        # normal event end time
        remains_sr = res_sr.apply(lambda x: type(x) == str)
        res_sr[remains_sr] = in_df[remains_sr]["終了日"].apply(make_date_str_T21)
    
    return res_sr


def get_event_table():
    try:
        pjsekai_res = requests.get("https://pjsekai.com/?2d384281f1")
        if pjsekai_res.ok:

            a = pd.read_html(pjsekai_res.content, index_col='No', encoding="utf-8",
                            attrs={"id": "sortable_table1"})[0]
            # default columns belown
            # No, 週目, イベント名, 形式, ユニット, タイプ, 書き下ろし楽曲, 開始日, 終了日, 日数, 参加人数
            
            # a["ユニット"] = a["ユニット"].apply(unit_name_convert)
            a["開始日"] = date_convert(a, start=True)
            a["終了日"] = date_convert(a, end=True)
            

            
            # a.to_csv("./event_data.csv", index=False, header=False)
            return a
        else:
            raise ValueError("status code: " + str(pjsekai_res.status_code))
    except Exception as e:
        print("ERROR at fetchig event table")
        print(e)
        return pd.DataFrame(columns=["開始日", "終了日", "イベント名"])


def get_stream_table():
    try:
        pjsekai_res = requests.get("https://pjsekai.com/?1c5f55649f")
        if pjsekai_res.ok:
            a = pd.read_html(pjsekai_res.content, 
                        encoding="utf-8",
                        attrs={"border": "0", "cellspacing": "1", "class": "style_table"})
            # print(a[0])

            a_temp = a[0][["No", "配信日時"]]
            a_temp.columns = ["No", "配信日時"]
            # print(a_temp)
            a_temp = a_temp.drop_duplicates(ignore_index=True)

            # convert Japanese datetime string to datetime object
            a_temp["配信日時"] = a_temp["配信日時"].apply(read_date_str)
            a_temp.loc[:, "No"] = a_temp["No"].apply(lambda x: "プロセカ放送局 " + x)

            # Be careful that No column includes the description of the stream
            return a_temp
        else:
            raise ValueError("status code: " + str(pjsekai_res.status_code))
    except Exception as e:
        print("ERROR at fetchig stream table")
        print(e)
        return pd.DataFrame(columns=["No", "配信日時"])

test_table = get_stream_table()
# print(test_table)

if __name__ == "__main__":
    print("##### stream table #####")
    # print(get_stream_table().to_markdown())
    print()
    print("##### event table #####")
    # print(get_event_table().to_markdown())
