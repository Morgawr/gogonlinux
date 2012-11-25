import json
import os
import getpass
import gog_filelock as FileLock

filelock_path = os.path.join("/var", "lock", getpass.getuser())

class GogDatabase:

    #this is a dictionary of all game data
    games = {}

    def __init__(self, dbfile):
        self.dbpath = dbfile
        if not os.path.exists(self.dbpath):
            f = open(self.dbpath, 'w')
            f.write("{ }")
            f.close()

    #reloads the database from the json file discarding any unstored changes
    def update(self):
        f = open(self.dbpath)
        data = json.load(f)
        f.close()
        self.games = {}
        for name, content in data.items():
            self.games[name] = GameRecord(name, content)

    #stores changes to the local database file, on the filesystem
    def store(self):
        # Locking for race condition purposes
        with FileLock.FileLock(os.path.basename(self.dbpath), filelock_path):
            f = open(self.dbpath, 'w')
            f.write(json.dumps(self.games, indent=4, default=GameRecord.serialize))
            f.close()

    def remove_game(self, name):
        if self.has_game(name):
            del self.games[name]

    def add_game(self, name, game):
        if not self.has_game(name):
            self.games[name] = game

    def has_game(self, name):
        if name in self.games.keys():
            return True
        return False


class GameRecord(json.JSONEncoder):

    install_path = None
    install_script = None
    uninstall_script = None
    launch_script = None
    install_script_file = None
    uninstall_script_file = None
    online_id = None
    full_name = None
    emulation = None
    cover_url = None
    compat = "red"
    released = '1'

    def __init__(self, name, data=None):
        self.full_name = name
        if data != None:
            if "install_path" in data.keys():
                self.install_path = data["install_path"]
            self.install_script = data["install_script"]
            self.launch_script = data["launch_script"]
            self.uninstall_script = data["uninstall_script"]
            if "install_script_file" in data.keys():
                self.install_script_file = data["install_script_file"]
            if "uninstall_script_file" in data.keys():
                self.uninstall_script_file = data["uninstall_script_file"]
            if "online_id" in data.keys():
                self.online_id = data["online_id"]
            if "full_name" in data.keys():
                self.full_name = data["full_name"]
            if "released" in data.keys():
                self.released = data["released"]
            self.emulation = data["emulation"]
            self.cover_url = data["cover_url"]
            self.compat = data["compat"]
    
    @staticmethod
    def serialize(obj):
        data = {}
        data["install_path"] = obj.install_path
        data["install_script"] = obj.install_script
        data["uninstall_script"] = obj.uninstall_script
        data["launch_script"] = obj.launch_script
        data["install_script_file"] = obj.install_script_file
        data["uninstall_script_file"] = obj.uninstall_script_file
        data["online_id"] = obj.online_id
        data["emulation"] = obj.emulation
        data["cover_url"] = obj.cover_url
        data["compat"] = obj.compat
        data["full_name"] = obj.full_name
        data["released"] = obj.released
        return data

