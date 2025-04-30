import requests
import os
from time import sleep

def main(ids):
  channel_id = "1201803456130863136"
  base_url = "https://discord.com/api/v10/"
  api_str = f"channels/{channel_id}/messages"

  DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
  
  for id in ids:

    data = {"content": f"https://vxtwitter.com/pj_sekai/status/{id}"}
    
    response = requests.post(
      base_url + api_str,
      headers={
        'Authorization': f'Bot {DISCORD_TOKEN}'
      },
      data=data
    )
    
    if not response.ok:
      print("ERROR: discord post failed?")
      print("status code: " + str(response.status_code))
      print(response.text)
      break
    
    sleep(1)