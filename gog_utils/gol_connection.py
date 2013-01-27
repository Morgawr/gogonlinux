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

def obtain_available_games(beta, repo=None):
    """ 
    Return JSON list of all available games. If no repo is specified
    then return the official one. Beta status only works for official repo.
    """
    if repo is not None:
        site = repo
    elif beta:
        site = "%s%s" % (WEBSITE_URL, BETA_GAMES)
    else:
        site = "%s%s" % (WEBSITE_URL, AVAILABLE_GAMES)
    if (site.startswith("http://") or site.startswith("https://") or
        site.startswith("www.")):
        resp = requests.get(url=site)
        if resp.status_code != 200:
            raise Exception("The game repository could not be found")
        return json.loads(resp.text)
    path = os.path.join(os.getcwd(),site)
    if not os.path.isfile(path):
        raise Exception("The local game repository could not be found")
    with  open(path) as localfile:
        return json.loads(localfile.read()) #pylint: disable=E1103

def generate_dummy_data(game_id):
    """
    Create fake JSON data for games that aren't yet supported by 
    any existing repository.
    """
    data = {}
    data["install_script"] = "404"
    data["launch_script"] = "404"
    data["uninstall_script"] = "404"
    data["online_id"] = game_id
    data["title"] = game_id
    data["released"] = '1'
    data["emulation"] = "unknown"
    data["cover_url"] = "http://gogonlinux.com/images/empty_cover.jpg"
    data["compat"] = "red"
    data["private_repository"] = '1'
    data["repository_url"] = "forced"
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
