import json

class UserData:

    def __init__(self, data):
        self.__parse_data(json.loads(data))

    #takes a string of json code and retrieves useful data
    def __parse_data(self, data):
        user = data["user"]
        self.name = user["xywka"]
        self.email = user["email"]
        self.forum = str(user["notifications"]["forum"])
        self.games = str(user["notifications"]["games"])
        self.messages = str(user["notifications"]["messages"])
        self.imagebig = user["avatar"]["big"]
        self.imagesmall = user["avatar"]["small"]

