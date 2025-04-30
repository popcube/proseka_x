import csv
from datetime import datetime, timezone, timedelta
import re

weekday_dict = {
  0: "日",
  1: "月",
  2: "火",
  3: "水",
  4: "木",
  5: "金",
  6: "土"
}

# format change from ISO YYYY-mm-ddTHH:MM:SS to mm/dd（曜日） HH:MM
def datetime_str_ja(iso_str):
  dt_temp = datetime.fromisoformat(iso_str)
  return dt_temp.strftime("%m/%d（") + weekday_dict[dt_temp.weekday()] + dt_temp.strftime("） %H:%M")
  

def decorate_row(row):
  
  row_0_txt = datetime_str_ja(row[0])
  row_0_url = f'https://twitter.com/pj_sekai/status/{row[1]}'
  row_0 = f'[{row_0_txt}]({row_0_url})'
  
  # # extract the strings that start with http or https and end with whitespace, line break or end of text
  # # then replace them to [LINK](url) format
  # row_2 = re.sub(r"(https?://[^\s]+)(?=\s|$)", r"[LINK](\1)", row[2])
  # # replace all consecutive whitespace and line break to single whitespace
  # row_2 = re.sub(r"\s+", " ", row_2)
  
  # return f"\n---\n\n**DATE**: {row_0}\n<br>\n{row_2}"
  return f"\n---\n\n**DATE**: {row_0}\n<br>\n{row[2][:5]}..."

def decorate_row_widget(row):

  row_0_txt = datetime_str_ja(row[0])
  row_0_url = f'https://twitter.com/pj_sekai/status/{row[1]}'
  # row_0 = f'[{row_0_txt}]({row_0_url})'
  
  # use twitter widget
  row_2 = f'<blockquote class="twitter-tweet">\n<a href="{row_0_url}"></a>\n</blockquote>'
  
  return f"\n---\n\n**DATE**: {row_0_txt}\n<br>\n{row_2}"

def main():

  res = []
  res.append("")
  res.append("## プロセカX(旧Twitter) 投稿記録")
  res.append("### 最終更新：" + datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime("%Y/%m/%d %H:%M"))
  res.append("")
  # res.append("|Date Link|Content|")
  # res.append("| ---- | ---- |")

  with open(
    "./docs/sorted_data.csv", "r",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    reader = csv.reader(f)
    
    # skip csv header
    next(reader)
    
    for i, row in enumerate(reader):
      if i < 5:
        res.append(decorate_row_widget(row))
      else:
        res.append(decorate_row(row))
        
    
    res.append("")
    res.append('<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')
      
  with open(
    "./docs/index.md", "w",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    f.writelines([r + "\n" for r in res])
    
if __name__ == '__main__':
  main()