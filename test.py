import re
from datetime import datetime, timedelta
import pandas as pd
maint_datetime_match = re.compile(r'(\d{1,2})月(\d{1,2})日[^\d]+(\d{1,2}:\d{2})[^\d]+(\d{1,2}:\d{2}).*')
raw_post_table = pd.read_csv("./sorted_data.csv", parse_dates=["POST DATE"], date_format="ISO8601")

def testfunc(in_text):
  in_line_list = in_text.split("\n")
  if in_line_list[0] != "【メンテナンス実施のお知らせ】":
    return False
  
  for in_line in in_line_list[1:]:
    try:
      # print(re.match(maint_datetime_match, in_line))
      dt_match = maint_datetime_match.search(re.sub(r'\s+', '', in_line))
      if dt_match:
        break
    except:
      continue
  else:
    return False
  
  month, day, start_time, end_time = dt_match.groups()
  
  if datetime.now().month >= 11 and month <= 2:
    year = datetime.now().year + 1
  else:
    year = datetime.now().year
  
  start_datetime = datetime.strptime(f"{year}-{month}-{day} {start_time}", "%Y-%m-%d %H:%M")
  end_datetime = datetime.strptime(f"{year}-{month}-{day} {end_time}", "%Y-%m-%d %H:%M")
  
  return start_datetime, end_datetime


samples = raw_post_table
now =datetime.now() + timedelta(days=-66, hours=-4, minutes=30)
print(samples["BODY TEXT"][samples["BODY TEXT"].str.startswith("【メンテナンス実施のお知らせ】")])
raw_datetime_ds = samples["BODY TEXT"].apply(testfunc)
datetime_df = raw_datetime_ds[raw_datetime_ds.apply(bool)].apply(pd.Series)
datetime_df.columns = ['START', 'END']
notice_df = datetime_df[datetime_df["END"].ge(now)]
for row in notice_df.itertuples():
  if row.START < now:
    print("WARN", row)
    print(row.Index)
    print(samples.loc[row.Index, "POST ID"])
  else:
    print(row)


datetime_df.sort_values(by="START", ascending=False, inplace=True)
print(now)