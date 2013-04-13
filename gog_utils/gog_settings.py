""" Module that handles all stuff related to local app settings. """

import os
import ConfigParser


class GogSettings:
    """ This class keeps all the data relevant to local app settings. """

    configfile = ""
    data = {}

    # creates new settings if they don't already exit
    def __init__(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        self.configfile = os.path.join(path, "config")
        if not os.path.exists(self.configfile):
            self.obtain_default()
            self.store()
        else:
            self.load()

    def obtain_default(self):
        """ Obtain default settings. """
        self.data["install_path"] = os.path.join(os.getenv("HOME"),
                                                 "games", "gog")
        self.data["use_virtual_desktop"] = False
        self.data["profile_update"] = 120
        self.data["virtual_resolution"] = "800x600"
        self.data["access_beta"] = False

    def load(self):
        """ Load settings from the filesystem. """
        parser = ConfigParser.ConfigParser()
        parser.read(self.configfile)
        section = "settings"
        for opt in parser.options(section):
            try:
                self.data[opt] = parser.get(section, opt)
            except:
                print "Exception in config parsing on %s " % opt
                self.data[opt] = None

    def store(self):
        """ Store settings from the instance to the filesystem. """
        path = os.path.join(os.getenv("HOME"), ".gog-tux")
        if not os.path.exists(path):
            os.makedirs(path)
        configfile = os.path.join(path, "config")
        parser = ConfigParser.ConfigParser()
        section = "settings"
        parser.add_section(section)
        parser.set(section, "install_path", self.data["install_path"])
        parser.set(section, "use_virtual_desktop",
                   self.data["use_virtual_desktop"])
        parser.set(section, "virtual_resolution",
                   self.data["virtual_resolution"])
        parser.set(section, "profile_update", self.data["profile_update"])
        parser.set(section, "access_beta", self.data["access_beta"])
        if "token" in self.data and "key" in self.data:
            parser.set(section, "token", self.data["token"])
            parser.set(section, "key", self.data["key"])
        file_handle = open(configfile, 'w+')
        parser.write(file_handle)
        file_handle.close()
