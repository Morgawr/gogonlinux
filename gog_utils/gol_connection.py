import json
import requests
import os
import stat

website_url = "http://www.gogonlinux.com"
available_games = "/available"

#returns the json list of all available games
def obtain_available_games():
    resp = requests.get(url=(website_url+available_games))
    return json.loads(resp.text)

def obtain_install_url(game_id):
    data = obtain_available_games()
    return data[game_id]["install_script"]

def obtain_uninstall_url(game_id):
    data = obtain_available_games()
    return data[game_id]["uninstall_script"]

def obtain_launch_url(game_id):
    data = obtain_available_games()
    return data[game_id]["launch_script"]

def download_script(target, url):
    r = requests.get(url)
    with open(target,"w+") as f:
        f.write(r.content)
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
