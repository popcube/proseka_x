import os, sys
from datetime import datetime, timedelta
import json
import csv
import re

from make_index_md_3 import main as make_index_md
from send_to_discord import main as send_to_discord
from private_script_storage.populate_from_ids import main as populate_from_ids

GITHUB_EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH")
GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT")

def get_current_data():
  with open(
    "./docs/sorted_data.csv", "r",
    encoding='utf-8',
    errors='ignore'
  ) as f:
    reader = csv.reader(f)
    
    # skip header
    return [r for r in reader][1:]

def datetime_str(dt_str):
  dt = datetime.fromisoformat(dt_str.rstrip("Z")) + timedelta(hours=+9)
  return dt.isoformat()

if __name__ == '__main__':
  event_dict = dict()
  with open(GITHUB_EVENT_PATH, "r") as f:
    event_dict = json.loads(f.read())
  retention_days = 94
  
  cur_posts = get_current_data()
  # print(cur_posts)
  
  cutoff_date = datetime.now() + timedelta(days= -1 * retention_days)
  
  ## cut the old data using date criteria
  cur_posts = [post for post in cur_posts
               if datetime.fromisoformat(post[0]) > cutoff_date]
  
  gt = event_dict["inputs"]["gt"]
  ids_raw = event_dict["inputs"]["ids"].split()
  ids = []
  
  ## parse url to id when necessary
  url_pattern = r"^https://(x|twitter)\.com/pj_sekai/status/([0-9]+)($|\?.+)"
  for id in ids_raw:
    if re.fullmatch(r"^[0-9]+$", id):
      ids.append(id)
    elif re.fullmatch(url_pattern, id):
      ids.append(re.match(url_pattern, id).group(2))
      
  new_posts = populate_from_ids(gt, ids)
  
  ## all posts including dupe entry
  all_posts = cur_posts + new_posts
  
  cur_ids = [r[1] for r in cur_posts]
  new_ids = list(set([r[1] for r in new_posts]))
  # new post ids that are not in the current list
  added_ids = [id for id in new_ids if id not in cur_ids]
  
  # when new post is detected
  if len(added_ids) > 0:
  # if True:
    
    added_ids.sort(reverse=True)
    send_to_discord(added_ids)
    
    added_posts = []    
    
    print()
    print("########## New posts ##########")
    for post in new_posts:
      ## get only added posts AND unique ids
      if post[1] in added_ids and post[1] not in [post_pre[1] for post_pre in added_posts]:
        added_posts.append(post)
        print(post[:2])
    print()
    
    posts = cur_posts + added_posts
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
    
    make_index_md()
    
    with open(
      "./sorted_data_viewer.csv", "w",
      encoding='utf-8',
      errors='ignore'
    ) as f:
      writer = csv.writer(f)
      writer.writerows([item.replace("\n", " ") for item in post] for post in posts)
    
    if len(GITHUB_OUTPUT) > 0:
      with open(GITHUB_OUTPUT, "a") as f:
        f.write("CHANGE=YES\n")
  
  else:
    print("No new post detected")
    
    
  
