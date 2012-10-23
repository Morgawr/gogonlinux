import json
import os

class GogDatabase:

    #this is a dictionary of all game data
    games = {}

    def __init__(self, dbfile):
        self.dbpath = dbfile
        if not os.path.exists(self.dbpath):
            open(self.dbpath, 'w').close()
            
        

    #reloads the database from the json file discarding any unstored changes
    def update(self):
        f = open(self.dbpath)
        data = json.load(f)
        f.close()
        for name, content in data.items():
            self.games[name] = GameRecord(name,content)


    #stores changes to the local database file, on the filesystem
    def store(self):
        f = open(self.dbpath,'w')
        f.write(json.dumps(self.games, indent=4, default=GameRecord.serialize))
        f.close()


class GameRecord(json.JSONEncoder):

    install_path = None
    install_script = None
    uninstall_script = None
    setup_path = None
    online_id = None
    emulation = None
    cover_url = None

    def __init__(self, name, data):
        self.gamename = name
        self.install_path = data["install_path"]
        self.install_script = data["install_script"]
        self.uninstall_script = data["uninstall_script"]
        self.setup_path = data["setup_exe"]
        self.online_id = data["online_id"]
        self.emulation = data["emulation_mode"]
        self.cover_url = data["cover_url"]
    
    @staticmethod
    def serialize(obj):
        data = {}
        data["install_path"] = obj.install_path
        data["install_script"] = obj.install_script
        data["uninstall_script"] = obj.uninstall_script
        data["setup_exe"] = obj.setup_path
        data["online_id"] = obj.online_id
        data["emulation_mode"] = obj.emulation
        data["cover_url"] = obj.cover_url
        return data

