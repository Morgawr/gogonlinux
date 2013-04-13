"""
Module representing the database where all the game info is stored.

This module also represents the game records that are stored in the database.

"""

import json
import os
import getpass
import hashlib

import gog_utils.gog_filelock as FileLock

FILELOCK_PATH = os.path.join("/tmp", "lock", getpass.getuser())


class GogDatabase:
    """ Class representing the game database. """

    # This is a dictionary of all game data
    games = {}

    def __init__(self, dbfile):
        self.dbpath = dbfile
        if not os.path.exists(self.dbpath):
            file_handle = open(self.dbpath, 'w')
            file_handle.write("{ }")
            file_handle.close()

    def update(self):
        """
        Reload the database from the JSON file discarding any unstored changes.
        """
        with FileLock.FileLock(os.path.basename(self.dbpath), FILELOCK_PATH):
            file_handle = open(self.dbpath)
            data = json.load(file_handle)
            file_handle.close()
        self.games = {}
        for name, content in data.items():
            self.games[name] = GameRecord(name, content)

    def store(self):
        """ Store changes to the local database file, on the filesystem. """
        # Locking for race condition purposes
        with FileLock.FileLock(os.path.basename(self.dbpath), FILELOCK_PATH):
            file_handle = open(self.dbpath, 'w')
            file_handle.write(json.dumps(self.games, indent=4,
                                         default=GameRecord.serialize))
            file_handle.close()

    def remove_game(self, name):
        """ Remove a game from the database. """
        if self.has_game(name):
            del self.games[name]

    def add_game(self, name, game):
        """ Add a game to the database. """
        if not self.has_game(name):
            self.games[name] = game

    def has_game(self, name):
        """
        Check whether a game is in the database.
        This basically means whether the game is
        installed or not
        """
        if name in self.games:
            return True
        return False


class GameRecord(json.JSONEncoder):
    """ Class representing a game record in the database. """
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
    private = '0'
    repo_url = 'official'

    def __init__(self, name, data=None):
        self.full_name = name
        if data != None:
            if "install_path" in data:
                self.install_path = data["install_path"]
            self.install_script = data["install_script"]
            self.launch_script = data["launch_script"]
            self.uninstall_script = data["uninstall_script"]
            if "install_script_file" in data:
                self.install_script_file = data["install_script_file"]
            if "uninstall_script_file" in data:
                self.uninstall_script_file = data["uninstall_script_file"]
            if "online_id" in data:
                self.online_id = data["online_id"]
            if "full_name" in data:
                self.full_name = data["full_name"]
            if "released" in data:
                self.released = data["released"]
            if "private_repository" in data:
                self.private = data["private_repository"]
                self.repo_url = data["repository_url"]
            self.emulation = data["emulation"]
            self.cover_url = data["cover_url"]
            self.compat = data["compat"]

    def obtain_launcher_md5(self):
        """
        Check the md5 digest on the locally installed launcher script for the
        related game record.
        """
        path = os.path.join(self.install_path, "startgame.sh")
        if not os.path.exists(path):
            return ""
        file_handle = open(path, 'r')
        data = file_handle.read()
        file_handle.close()
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def serialize(obj):
        """ Serialize a GameRecord object. """
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
        data["private_repository"] = obj.private
        data["repository_url"] = obj.repo_url
        return data
