""" 
Module hosting class representing the connection data
to the gogonlinux website
"""

import json
import requests
import os
import stat

WEBSITE_URL = "http://www.gogonlinux.com"
AVAILABLE_GAMES = "/available"
BETA_GAMES = "/available-beta"

def obtain_available_games():
    """ Return JSON list of all available games. """
    resp = requests.get(url=(WEBSITE_URL + AVAILABLE_GAMES))
    return json.loads(resp.text) #pylint: disable=E1103

def obtain_beta_available_games():
    """
    Obtain JSON list of all available games, even 
    the ones flagged as beta/unreleased
    """
    resp = requests.get(url=(WEBSITE_URL + BETA_GAMES))
    return json.loads(resp.text) #pylint: disable=E1103

def generate_dummy_data(game_id):
    """
    Create fake JSON data for games that aren't yet supported by 
    any existing repository.
    """
    data = {}
    data[game_id] = {}
    data[game_id]["install_script"] = "404"
    data[game_id]["launch_script"] = "404"
    data[game_id]["uninstall_script"] = "404"
    data[game_id]["online_id"] = game_id
    data[game_id]["full_name"] = game_id
    data[game_id]["released"] = '1'
    data[game_id]["emulation"] = "unknown"
    data[game_id]["cover_url"] = "http://gogonlinux.com/images/empty_cover.jpg"
    data[game_id]["compat"] = "red"
    data[game_id]["private_repository"] = '1'
    data[game_id]["repository_url"] = "forced"
    return json.loads(json.dumps(data))


def download_script(target, url):
    """ 
    Download a script from the gogonlinux url
    and save it to the target position
    """
    reqs = requests.get(url)
    with open(target, "w+") as file_handle:
        file_handle.write(reqs.content) #pylint: disable=E1103
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

def obtain_launch_md5_list():
    """
    Download the data from the md5 list of launcher scripts on gogonlinux to
    check if there are new updates for each individual game.
    """
    try:
        resp = requests.get(url=(WEBSITE_URL + "/launcher_md5"))
        return json.loads(resp.text)
    except requests.ConnectionError:
        return "{}"
