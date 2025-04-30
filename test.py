import re
from datetime import datetime
import pandas as pd
maint_datetime_match = r'(\d{1,2})月(\d{1,2})日[^\d]+(\d{1,2}:\d{1,2})[^\d]+(\d{1,2}:\d{1,2}).+'
raw_post_table = pd.read_csv("./sorted_data.csv",                   parse_dates=["POST DATE"],                   date_format="ISO8601")

def testfunc(in_text):
  in_line_list = in_text.split("\n")
  if in_line_list[0] != "【メンテナンス実施のお知らせ】":
    return False
  
  for in_line in in_line_list[1:]:
    try:
      print(re.match(maint_datetime_match, in_line))
      dt_match = re.match(maint_datetime_match, re.sub(r'\s+', '', in_line))
      if dt_match:
        break
    except:
      continue
  else:
    
    print(in_line_list)
    return False
  
  month, day, start_time, end_time = dt_match.groups()
  
  if datetime.now().month >= 11 and month <= 2:
    year = datetime.now().year + 1
  else:
    year = datetime.now().year
  
  start_datetime = datetime.strptime(f"{year}-{month}-{day} {start_time}", "%Y-%m-%d %H:%M")
  end_datetime = datetime.strptime(f"{year}-{month}-{day} {end_time}", "%Y-%m-%d %H:%M")
  
  return start_datetime, end_datetime


samples = raw_post_table["BODY TEXT"]
print(samples[samples.str.startswith("【メンテナンス実施のお知らせ】")])
for sample in samples:
    a = testfunc(sample)
    if a:
        print(a)