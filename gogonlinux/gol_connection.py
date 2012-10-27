import json
import requests

website_url = "http://www.gogonlinux.com"
available_games = "/games/available"

#returns the json list of all available games
def obtain_available_games():
    resp = requests.get(url=(website_url+available_games))
    return json.loads(resp.text)
