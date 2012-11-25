"""Module hosting class representing connection to GoL."""

import json
import requests
import os
import stat

WEBSITE_URL = "http://www.gogonlinux.com"
AVAILABLE_GAMES = "/available"
BETA_GAMES = "/available-beta"

def obtain_available_games():
    """Returns JSON list of all available games."""
    resp = requests.get(url=(WEBSITE_URL + AVAILABLE_GAMES))
    return json.loads(resp.text) #pylint: disable=E1103

def obtain_beta_available_games():
    """Obtains JSON list of all available beta games."""
    resp = requests.get(url=(WEBSITE_URL + BETA_GAMES))
    return json.loads(resp.text) #pylint: disable=E1103

def download_script(target, url):
    """Function to download data from url to target."""
    reqs = requests.get(url)
    with open(target, "w+") as file_handle:
        file_handle.write(reqs.content) #pylint: disable=E1103
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
