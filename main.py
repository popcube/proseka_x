import os, sys
from datetime import datetime, timedelta
import json
import csv
# import collections

from time import sleep
from googleapiclient.discovery import build

from make_index_md_3 import main as make_index_md
from send_to_discord import main as send_to_discord

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID")
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

def get_search_response(days, keyword, max_page, ex_urls):
  service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

  start_index = 1
  response = []
  for n_page in range(max_page):
    try:
      response.append(service.cse().list(
        cx=SEARCH_ENGINE_ID,
        num=10,
        q=keyword,
        siteSearch=" ".join(ex_urls),
        siteSearchFilter='e',
        dateRestrict=f'd{days}',
        sort='socialmediaposting-datepublished', # + ':r:20240101:20240125' for date restriction but scarce results
        start=start_index
      ).execute())
      if "nextPage" in response[n_page]["queries"]:
        start_index = response[n_page]["queries"]["nextPage"][0]["startIndex"]
        sleep(1)
        continue
      else:
        print("consumed pages: " + str(n_page+1))
        break
    except Exception as e:
      print(e)
      break

  jsonstr = json.dumps(response, indent=2, ensure_ascii=False)
  with open(
    'out.json',
    mode='w',
    encoding='utf-8',
    errors='ignore'
  ) as response_file:
    response_file.write(jsonstr)

  return response

def datetime_str(dt_str):
  dt = datetime.fromisoformat(dt_str.rstrip("Z")) + timedelta(hours=+9)
  return dt.isoformat()

def detect_rt(post_list, person_list, og_description):
  post_flag = len(post_list) >= 2
  person_flag = len(person_list) >= 2
  description_flag = og_description.startswith("RT @")
  return post_flag and person_flag and description_flag
  
def post_sort(response):
  sorted_posts = []
  try:
    total_results = response[0]["queries"]["request"][0]["totalResults"]
    print()
    print(f"total results: {total_results}")
    print(f"max page: {max_page}")
    print()

  except Exception as e:
    print(e)
    print("no search results?")
    print()

  else:
    now_str = (datetime.now() + timedelta(hours=9)).isoformat()
    for res in response:
      for item in res["items"]:
        try:
          post_obj_list = item["pagemap"]["socialmediaposting"]
          metatag_body = item["pagemap"]["metatags"][0]["og:description"]
          person_obj_list = item["pagemap"]["person"]
          post_id = post_obj_list[0]["identifier"]
          if detect_rt(post_obj_list, person_obj_list, metatag_body):
            print(f"{post_id} is evaluated as Repost, skipping...")
            continue
          
          sorted_posts.append([
            datetime_str(post_obj_list[0]["datecreated"]),        ## date
            post_id,                                              ## id
            # post_obj["articlebody"].rstrip("Translate post"),     ## body
            metatag_body,                                         ## metatag body
            now_str                                               ## detected time
          ])
        except Exception as e:
          print(e)
          print("cannot retrieve item from out.json, skipping...")
          pass
          
    sorted_posts.sort(key=lambda x: x[1], reverse=True)

  return sorted_posts


if __name__ == '__main__':
  ########################################
  ## define search query and parameters ##
  ########################################
  max_page = int(os.environ.get("MAX_PAGES", 1))
  # max_page = 10
  # minimum date or search range
  days = 1 if max_page == 1 else 3
  keyword = "プロジェクトセカイ"
  base_url = "https://twitter.com/pj_sekai/status/"
  base_url_2 = "https://x.com/pj_sekai/status/"
  retention_days = 94
  ########################################
  
  cur_posts = get_current_data()
  # print(cur_posts)
  
  cutoff_date = datetime.now() + timedelta(days= -1 * retention_days)
  search_date = datetime.now() + timedelta(days= -1 * days)
  
  ## cut the old data using date criteria
  cur_posts = [post for post in cur_posts
               if datetime.fromisoformat(post[0]) > cutoff_date]
  
  ## create urls to be excluded from next g search
  ex_urls = [base_url + post[1] for post in cur_posts
             if datetime.fromisoformat(post[0]) > search_date]
  ex_urls += [base_url_2 + post[1] for post in cur_posts
             if datetime.fromisoformat(post[0]) > search_date]
  
  res = get_search_response(days, keyword, max_page, ex_urls)
  new_posts = post_sort(res)
  
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
    
    
  
