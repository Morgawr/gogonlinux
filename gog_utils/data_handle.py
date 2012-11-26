""" Modules that handles and parses user data from gog.com. """

import json

class UserData:
    """ Class to handle user data from gog.com """

    name = None
    email = None
    forum = None
    games = None
    messages = None
    imagebig = None
    imagesmall = None

    def __init__(self, data):
        self.__parse_data(json.loads(data))

    def __parse_data(self, data):
        """ Parse data taking a string of JSON code. """
        user = data["user"]
        self.name = user["xywka"]
        self.email = user["email"]
        self.forum = str(user["notifications"]["forum"])
        self.games = str(user["notifications"]["games"])
        self.messages = str(user["notifications"]["messages"])
        self.imagebig = user["avatar"]["big"]
        self.imagesmall = user["avatar"]["small"]

