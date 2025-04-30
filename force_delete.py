import os, sys
import re
import json
import csv

GITHUB_EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH")

def get_current_data():
  with open(
    "./docs/sorted_data.csv", "r",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    reader = csv.reader(f)
    
    # skip header
    return [r for r in reader][1:]

event_dict = dict()
with open(GITHUB_EVENT_PATH, "r") as f:
  event_dict = json.loads(f.read())
ids_raw = event_dict["inputs"]["ids"].split()
ids = []

## parse url to id when necessary
url_pattern = r"^https://(x|twitter)\.com/pj_sekai/status/([0-9]+)($|\?.+)"
for id in ids_raw:
  if re.fullmatch(r"^[0-9]+$", id):
    ids.append(id)
  elif re.fullmatch(url_pattern, id):
    ids.append(re.match(url_pattern, id).group(2))

print()
print("##### TO BE DELETED IDS #####")
for id in ids:
  print(id)


posts = get_current_data()
posts = [post for post in posts if post[1] not in ids]

posts.sort(key=lambda x: x[1], reverse=True)

# add header for output
posts.insert(0, ["POST DATE", "POST ID", "BODY TEXT", "DETECTED DATE"])
# post_strs = [",".join(post.values()) + "\n" for post in posts]
with open(
  "./docs/sorted_data.csv", "w",
  encoding='utf-8',
  errors='ignore'
) as f:
  writer = csv.writer(f)
  writer.writerows(posts)
  
with open(
  "./sorted_data_viewer.csv", "w",
  encoding='utf-8',
  errors='ignore'
) as f:
  writer = csv.writer(f)
  writer.writerows([item.replace("\n", " ") for item in post] for post in posts)