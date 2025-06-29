import csv, sys
from datetime import datetime, timezone, timedelta
import re
import pandas as pd
from get_event_table import get_event_table, get_stream_table

weekday_ja = ["月", "火", "水", "木", "金", "土", "日"]
maint_datetime_match = re.compile(r'(\d{1,2})月(\d{1,2})日[^\d]+(\d{1,2}:\d{2})[^\d]+(\d{1,2}:\d{2}).*')
timezone_jst = timezone(timedelta(hours=+9), name="JST")

def entry_format(in_dt, body):
  # format change from ISO YYYY-mm-ddTHH:MM:SS to mm/dd（曜日） HH:MM
  row_0_txt = in_dt.strftime("%m/%d（") + weekday_ja[in_dt.weekday()] + in_dt.strftime("） %H:%M")
  return f"\n---\n\n**DATE**: {row_0_txt}{body}"

def decorate_row(row):
  
  row_0_url = f'https://x.com/pj_sekai/status/{row["POST ID"]}'
  row_2 = f'[{row["BODY TEXT"][:5]}...]({row_0_url})'
  
  # # extract the strings that start with http or https and end with whitespace, line break or end of text
  # # then replace them to [LINK](url) format
  # row_2 = re.sub(r"(https?://[^\s]+)(?=\s|$)", r"[LINK](\1)", row[2])
  # # replace all consecutive whitespace and line break to single whitespace
  # row_2 = re.sub(r"\s+", " ", row_2)
  
  # extract hashtags
  row_tags = re.findall(r"\B#\w\w+\b", row["BODY TEXT"])
  row_tags_str = " ".join(
    tag for tag in row_tags
    if tag != "#プロセカ"
    and not re.fullmatch(r"\B#\d\w+\b", tag)
  )
  if len(row_tags_str) > 0:
    row_2 += "\n<br>\n" + row_tags_str
  
  # return f"\n---\n\n**DATE**: {row_0}\n<br>\n{row_2}"
  return entry_format(row["POST DATE"], "\n<br>\n" + row_2)

def decorate_row_widget(row):
  row_0_url = f'https://twitter.com/pj_sekai/status/{row["POST ID"]}'
  # row_0 = f'[{row_0_txt}]({row_0_url})'
  
  # use twitter widget
  row_2 = f'<blockquote class="twitter-tweet">\n<a href="{row_0_url}"></a>\n</blockquote>'
  
  return entry_format(row["POST DATE"], "\n<br>\n" + row_2)

def decorate_supplement(row):
  return entry_format(row.iat[0], row.iat[1])

def extract_two_datetimes(in_text):
  in_line_list = in_text.split("\n")
  if in_line_list[0] != "【メンテナンス実施のお知らせ】":
    return False
  
  for in_line in in_line_list[1:]:
    try:
      dt_match = maint_datetime_match.search(re.sub(r'\s+', '', in_line))
      if dt_match:
        break
    except:
      continue
  else:
    
    # print(in_line_list)
    return False
  
  month, day, start_time, end_time = dt_match.groups()
  
  if datetime.now().month >= 11 and month <= 2:
    year = datetime.now().year + 1
  else:
    year = datetime.now().year
  
  start_datetime = datetime.strptime(f"{year}-{month}-{day} {start_time}", "%Y-%m-%d %H:%M")
  end_datetime = datetime.strptime(f"{year}-{month}-{day} {end_time}", "%Y-%m-%d %H:%M")
  
  return start_datetime.replace(tzinfo=timezone_jst), end_datetime.replace(tzinfo=timezone_jst)

def main():

  now_dt = datetime.now(timezone_jst)
  # now_dt += timedelta(days=-66, hours=-6, minutes=-00) #delete this

  res = []
  res.append("")
  res.append("## プロセカX(旧Twitter) 投稿記録")
  res.append("当サイトは非公式です。プロセカ運営とは関係がありません。")
  res.append("### 最終更新：" + now_dt.strftime("%Y/%m/%d %H:%M"))
  res.append("")

  ## TEST BLOCK STARTS
  # print("ENTERED the script", flush=True)
  ## TEST BLOCK ENDS
  
  # header
  # POST DATE,POST ID,BODY TEXT,DETECTED DATE
  raw_post_table = pd.read_csv("./docs/sorted_data.csv",
                   parse_dates=["POST DATE"],
                   date_format="ISO8601")

  raw_datetime_ds = raw_post_table["BODY TEXT"].apply(extract_two_datetimes)
  datetime_df = raw_datetime_ds[raw_datetime_ds.apply(bool)].apply(pd.Series)
  datetime_df.columns = ['START', 'END']
  # notice_df = datetime_df[datetime_df["END"].ge(now_dt)].sort_values("START")
  notice_df = datetime_df.sort_values("START") # Switch this for testing 
  for id_num, row in enumerate(notice_df.itertuples()):
    res.append(f'<div class="highlight" id="maint-ongoing-{id_num}" style="display: none;"><div class="gd">')
    res.append("【メンテナンス実施中】")
    res.append("</div></div>")
    res.append(f'<div class="highlight" id="maint-planned-{id_num}" style="display: none;"><div class="gi">')
    res.append("【メンテナンス予定あり】")
    res.append("</div></div>")
    res.append(f'<div id="maint-{id_num}" style="display: none;">')
    if row.START.day != row.END.day:
      res.append(row.START.strftime("%m/%d（") 
                + weekday_ja[row.START.weekday()]
                + row.START.strftime("） %H:%M") 
                + " ～ "
                + row.END.strftime("%m/%d（") 
                + weekday_ja[row.END.weekday()]
                + row.END.strftime("） %H:%M"))
    else:
      res.append(row.START.strftime("%m/%d（") 
                + weekday_ja[row.START.weekday()]
                + row.START.strftime("） %H:%M") 
                + " ～ "
                + row.END.strftime("%H:%M"))
    source_url = f'https://x.com/pj_sekai/status/{raw_post_table.loc[row.Index, "POST ID"]}'
    res.append(f'[公式ポスト]({source_url})')
    res.append("　＊これはテストです") #delete this
    res.append("</div>")
    
    # print(row, flush=True)

  # get the oldest and lastest POST DATE as data cutoff
  oldest_date = raw_post_table.iloc[-1]["POST DATE"]
  latest_date = raw_post_table.loc[0, "POST DATE"]
  
  # create new empty column
  raw_post_table["text"] = ""
  # up to row 4, total 5 rows have widgets (loc assignment includes the assigned index too)
  raw_post_table.loc[:4, "text"] = raw_post_table.loc[:4].apply(decorate_row_widget, axis='columns')
  raw_post_table.loc[5:, "text"] = raw_post_table.loc[5:].apply(decorate_row, axis='columns')
  post_table = raw_post_table[["POST DATE", "text"]]
  post_table.set_index("POST DATE", inplace=True)
  
  event_table = get_event_table()
  stream_table = get_stream_table()
  
  if len(event_table) > 0:
    event_start_table = event_table[["開始日", "イベント名"]].copy()
    event_start_table.loc[:, "イベント名"] = event_start_table["イベント名"].apply(lambda x: " イベント「**" + x + "**」 開始")
    event_start_table["text"] = event_start_table.apply(decorate_supplement, axis='columns')
    event_start_table.set_index("開始日", inplace=True)
    event_end_table = event_table[["終了日", "イベント名"]].copy()
    event_end_table.loc[:, "イベント名"] = event_end_table["イベント名"].apply(lambda x: " イベント「**" + x + "**」 終了")
    event_end_table["text"] = event_end_table.apply(decorate_supplement, axis='columns')
    event_end_table.set_index("終了日", inplace=True)
  else:
    event_start_table = pd.DataFrame(columns=["text"])
    event_end_table = pd.DataFrame(columns=["text"])

  if len(stream_table) > 0:
    stream_table = stream_table[["配信日時", "No"]]
    stream_table["No"] = stream_table["No"].apply(lambda x: " 「**" + x + "**」 放送開始")
    stream_table["text"] = stream_table.apply(decorate_supplement, axis='columns')
    stream_table.set_index("配信日時", inplace=True)
  else:
    stream_table = pd.DataFrame(columns=["text"])
  
  res_df = pd.concat([post_table, event_start_table, event_end_table, stream_table])
  res_series = res_df["text"]
  
  # date cutoff
  res_series = res_series[(latest_date >= res_series.index) & (res_series.index >= oldest_date)]
  
  res_series.sort_index(inplace=True, ascending=False)
  
  # print(res_series)
  
  res += res_series.to_list()
  
  # res_table["text"].apply(lambda x: x.replace("\n", " ")).to_csv("testoutput.csv")
  
  # sys.exit(1)
    
  res.append("")
  res.append('<script async src="https://platform.twitter.com/widgets.js" charset="utf-8">')


    
  # js
  # let nowDt = new Date();
  # let startDt = new Date(row.START.year, row.START.month - 1, row.START.day, row.START.hour, row.START.minute);
  # let endDt = new Date(row.END.year, row.END.month - 1, row.END.day, row.END.hour, row.END.minute);
  
  # if (startDt < nowDt) && (nowDt < endDt){
  #   document.getElementById('maint-ongoing').style.display = 'block';
  #   document.getElementById('maint').style.display = 'block';
  # }
  # else if (nowDt < startDt){
  #   document.getElementById('maint-ongoing').style.display = 'block';
  #   document.getElementById('maint').style.display = 'block';
  # }
  res.append("let nowDt = new Date(2025, 6 - 1,23, 9);")
    # res.append("let nowDt = new Date(2025, );")

  for id_num, row in enumerate(notice_df.itertuples()):
    res.append(f"let startDt = new Date({row.START.year}, {row.START.month - 1}, {row.START.day}, {row.START.hour}, {row.START.minute});")
    res.append(f"let endDt = new Date({row.END.year}, {row.END.month - 1}, {row.END.day}, {row.END.hour}, {row.END.minute});")
    res.append("if (startDt < nowDt) && (nowDt < endDt){")
    res.append(f"  document.getElementById('maint-ongoing-{id_num}').style.display = 'block';")
    res.append(f"  document.getElementById('maint-{id_num}').style.display = 'block';")
    res.append("}")
    res.append("else if (nowDt < startDt){")
    res.append(f"  document.getElementById('maint-ongoing-{id_num}').style.display = 'block';")
    res.append(f"  document.getElementById('maint-{id_num}').style.display = 'block';")
    res.append("}") 
    
  res.append('</script>')
      
  with open(
    "./docs/index.md", "w",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    f.writelines(r + "\n" for r in res)
    
if __name__ == '__main__':
  main()
