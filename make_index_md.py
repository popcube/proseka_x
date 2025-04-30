import csv
from datetime import datetime
import re

def decorate_row_and_str(row):
  
  # format change from YYYY-mm-ddTHH:MM:SS to mm/dd<br>HH:MM
  # line break between date and time for visibility
  row_0_txt = datetime.fromisoformat(row[0]).strftime("%m/%d<br>%H:%M")
  row_0_url = f'https://twitter.com/pj_sekai/status/{row[1]}'
  row_0 = f'[{row_0_txt}]({row_0_url})'
  
  # extract the strings that start with http or https and end with whitespace, line break or end of text
  # then replace them to [LINK](url) format
  row_2 = re.sub(r"(https?://[^\s]+)(?=\s|$)", r"[LINK](\1)", row[2])
  # replace all consecutive whitespace and line break to single whitespace
  row_2 = re.sub(r"\s+", " ", row_2)
  
  return "|" + row_0  + "|" + row_2 + "|"

def main():

  res = []
  res.append("")
  res.append("## @pj_sekai recent posts")
  res.append("")
  res.append("|Date Link|Content|")
  res.append("| ---- | ---- |")

  with open(
    "./docs/sorted_data.csv", "r",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    reader = csv.reader(f)
    
    # skip header row
    header_flg = True
    for row in reader:
      if header_flg:
        header_flg = False
        continue
      res.append(decorate_row_and_str(row))
      
  with open(
    "./docs/index.md", "w",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    f.writelines([r + "\n" for r in res])