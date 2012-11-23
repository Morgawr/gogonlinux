import json
import requests
import os
import stat

website_url = "http://www.gogonlinux.com"
available_games = "/available"
beta_games = "/available-beta"

#returns the json list of all available games
def obtain_available_games():
    resp = requests.get(url=(website_url+available_games))
    return json.loads(resp.text)

def obtain_beta_available_games():
    resp = requests.get(url=(website_url+beta_games))
    return json.loads(resp.text)

def download_script(target, url):
    r = requests.get(url)
    with open(target,"w+") as f:
        f.write(r.content)
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
