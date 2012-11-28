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
