"""
Module specifying classes and methods to create and interact with the GUI
interface for gog-tux.

It holds the GUI mainwindow class, the Login window class and the window used
to output external commands and scripts.
"""

import os
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import gtk.glade
import threading
import urllib2
import subprocess
import signal
import json

import gog_utils.gog_db as gog_db
import gog_utils.gog_settings as gog_settings
import gog_utils.gol_connection as site_conn
import gog_utils.data_handle as data_handle
from gog_utils.version import version
from gog_utils.version import author
from gog_utils.version import email

PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.getenv("HOME"), ".gog-tux", "db.json")
CACHE_PATH = os.path.join(os.getenv("HOME"), ".gog-tux", "list.cache")
IMG_PATH = os.path.join(PACKAGE_DIRECTORY, "imgdata")
ICON = gtk.gdk.pixbuf_new_from_file(os.path.join(IMG_PATH, "gog-tux-icon.svg"))


# Let's init the gobject threading features.
gobject.threads_init()


class GogTuxGUI:
    """ Class representing the GUI interface for the main window of gog-tux. """
    # some image data
    compat = {}
    imgpath = os.path.join(PACKAGE_DIRECTORY, "imgdata")
    compat["green"] = gtk.gdk.pixbuf_new_from_file(os.path.join(IMG_PATH,
                                                                "green_compat.png"))
    compat["yellow"] = gtk.gdk.pixbuf_new_from_file(os.path.join(IMG_PATH,
                                                                 "yellow_compat.png"))
    compat["red"] = gtk.gdk.pixbuf_new_from_file(os.path.join(IMG_PATH,
                                                              "red_compat.png"))
    beta = gtk.gdk.pixbuf_new_from_file(os.path.join(IMG_PATH, "beta.png"))

    # some other default stuff
    islogged = False
    game_data = {}  # list of all available games from the website
    selected_game = None
    window_base_title = "Gog Linux Client - %s" % version

    def __init__(self, connection):
        self.connection = connection
        self.gladefile = os.path.join(PACKAGE_DIRECTORY, "gog_tux.glade")
        self.glade_tree = gtk.glade.XML(self.gladefile)
        self.rightpanel = self.glade_tree.get_widget("rightpanel")
        self.rightpanel.hide()
        if not os.path.exists(os.path.join(os.getenv("HOME"), ".gog-tux")):
            os.makedirs(os.path.join(os.getenv("HOME"), ".gog-tux"))
        self.database = gog_db.GogDatabase(DB_PATH)
        # This is a dictionary of all the signals handled by our GUI
        signals = {"on_gog_tux_destroy": gtk.main_quit,
                   "on_close_menu_activated": gtk.main_quit,
                   "on_about_menu_activated": self.about_menu_activated,
                   "on_undoprefsbutton_clicked": self.undo_settings,
                   "on_saveprefsbutton_clicked": self.save_settings,
                   "on_gog_tux_key_pressed": self.key_pressed,
                   "on_installbutton_activated": self.installbutton_activated,
                   "on_launchbutton_activated": self.launchbutton_activated,
                   "on_uninstallbutton_activated": self.uninstallbutton_activated,
                   "on_logoutmenu_activated": self.do_logout,
                   "on_loginmenu_activated": self.do_login,
                   "updatemenu_activated": self.check_for_updates}
        self.glade_tree.signal_autoconnect(signals)
        # obtain required resources
        self.window = self.glade_tree.get_widget("gog_tux")
        # set up gui elements
        self.init_gui_elements()
        # set up the lists for the games
        self.init_lists()
        # finalize initialization
        self.acquire_settings()
        self.have_beta_access = self.settings.data["access_beta"]
        self.do_load_games(False) # Read from cache first
        if self.check_cookies():
            token, key = self.obtain_cookies()
            self.connection.set_auth_token(token, key)
            self.logged_successfully()
        else:
            self.do_logout(None)
        self.window.show()
        self.load_games()
        self.undo_settings(None)

    def init_gui_elements(self):
        """
        Perform initialization of some gui elements taking them
        from the glade file and storing the into the class.
        """
        self.accountlabel = self.glade_tree.get_widget("accountlabel")
        self.emaillabel = self.glade_tree.get_widget("emaillabel")
        self.gamenotelabel = self.glade_tree.get_widget("gamenotelabel")
        self.forumnotelabel = self.glade_tree.get_widget("forumnotelabel")
        self.privatenotelabel = self.glade_tree.get_widget("privatenotelabel")
        self.profilepic = self.glade_tree.get_widget("profilepic")
        self.installpathentry = self.glade_tree.get_widget("installpathentry")
        self.virtualresentry = self.glade_tree.get_widget("resolutionentry")
        self.virtualdesktopcheck = self.glade_tree.get_widget(
            "virtualdesktopcheck")
        self.betasoftwarecheck = self.glade_tree.get_widget(
            "betasoftwarecheck")
        self.profileintervalentry = self.glade_tree.get_widget(
            "profileintervalentry")
        self.launchbutton = self.glade_tree.get_widget("launchbutton")
        self.installbutton = self.glade_tree.get_widget("installbutton")
        self.uninstallbutton = self.glade_tree.get_widget("uninstallbutton")
        self.gamenamelabel = self.glade_tree.get_widget("namelabel")
        self.gameinstalledlabel = self.glade_tree.get_widget("installedlabel")
        self.gameemulationlabel = self.glade_tree.get_widget("emulationlabel")
        self.gamerepositorylabel = self.glade_tree.get_widget(
            "repositorylabel")
        self.gamecoverimage = self.glade_tree.get_widget("coverimage")
        self.loginmenu = self.glade_tree.get_widget("loginmenu")
        self.logoutmenu = self.glade_tree.get_widget("logoutmenu")
        self.profiletablabel = self.glade_tree.get_widget("profiletablabel")
        self.profiletabpage = self.glade_tree.get_widget("profiletabpage")
        self.window.set_icon(ICON)

    # Performs initialization of the available and installed games lists
    def init_lists(self):
        """
        Perform initialization of the lists for available and
        installed games.
        """

        self.availablegamestree = self.glade_tree.get_widget(
            "availablegamestree")
        self.installedgamestree = self.glade_tree.get_widget(
            "installedgamestree")
        textrenderer = gtk.CellRendererText()
        imagerenderer = gtk.CellRendererPixbuf()
        columna = gtk.TreeViewColumn("Games", textrenderer, text=0)
        columnb = gtk.TreeViewColumn("Emulation mode", textrenderer, text=1)
        columnc = gtk.TreeViewColumn("Compatibility", imagerenderer)
        columnc.add_attribute(imagerenderer, "pixbuf", 2)
        inst_columna = gtk.TreeViewColumn("Games", textrenderer, text=0)
        inst_columnb = gtk.TreeViewColumn("Emulation mode",
                                          textrenderer, text=1)
        inst_columnc = gtk.TreeViewColumn("Compatibility", imagerenderer)
        inst_columnc.add_attribute(imagerenderer, "pixbuf", 2)

        # setup list of available games and installed games
        # 0 is the displayed name
        # 1 is emulation mode
        # 2 is visual representation of current compatibility state
        #                                                (green, yellow and red)
        # 3 is the game id in the lookup dictionary, not going to be displayed,
        #   just used for retrieval
        self.availgameslist = gtk.ListStore(gobject.TYPE_STRING,
                                            gobject.TYPE_STRING,
                                            gtk.gdk.Pixbuf,
                                            gobject.TYPE_STRING)
        self.installedgameslist = gtk.ListStore(gobject.TYPE_STRING,
                                                gobject.TYPE_STRING,
                                                gtk.gdk.Pixbuf,
                                                gobject.TYPE_STRING)
        self.availgameslist.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.installedgameslist.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.availablegamestree.set_model(self.availgameslist)
        self.availablegamestree.append_column(columna)
        self.availablegamestree.append_column(columnb)
        self.availablegamestree.append_column(columnc)
        self.installedgamestree.set_model(self.installedgameslist)
        self.installedgamestree.append_column(inst_columna)
        self.installedgamestree.append_column(inst_columnb)
        self.installedgamestree.append_column(inst_columnc)
        selection = self.availablegamestree.get_selection()
        selection.connect("changed", self.list_selection_changed,
                          self.availablegamestree)
        selection = self.installedgamestree.get_selection()
        selection.connect("changed", self.list_selection_changed,
                          self.installedgamestree)

    def about_menu_activated(self, widget):
        """ Create the about popup window. """
        about = gtk.AboutDialog()
        about.set_program_name("Gog Tux Client")
        about.set_version(version)
        about.set_copyright(author + " - " + email)
        about.set_comments("Unofficial Linux client for the gog.com platform")
        about.set_website("http://www.gogonlinux.com")
        about.set_logo(ICON)
        about.run()
        about.destroy()

    def list_selection_changed(self, widget, data):
        """
        Signal that reacts to either available or installed games list
        being clicked.
        """
        if data == self.availablegamestree or data == self.installedgamestree:
            self.rightpanel.show()
            items, paths = data.get_selection().get_selected_rows()
            if len(paths) == 0:
                self.rightpanel.hide()
                return
            element = items.get_iter(paths[0])
            if data == self.availablegamestree:
                game = self.game_data[items.get_value(element, 3)]
            else:
                # XXX: This should be refactored to be more pleasant
                game = self.database.games[items.get_value(element, 3)]
                game = gog_db.GameRecord.serialize(game)
                game["title"] = game["full_name"]  # for compatibility
                game = json.loads(json.dumps(game))
            self.show_game_card(game, items.get_value(element, 3))
        else:
            self.rightpanel.hide()

    def installbutton_activated(self, widget):
        """
        Function called when the install button has been clicked, we know
        the selected game is from the avilable games list and not from the
        installed games list because if the game is installed then we couldn't
        install it again.
        """
        if self.game_data[self.selected_game]["message"] != None:
            self.show_warning(self.game_data[self.selected_game]["message"])
        setup_file = None
        if self.islogged == True:
            dialog_text = "Do you want to use an already downloaded setup file?"
            yesno = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                      gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                      dialog_text)
            resp = yesno.run()
            yesno.destroy()
        if self.islogged == False or resp == gtk.RESPONSE_YES:
            # we need to create a filter for the .exe files
            setupfilter = gtk.FileFilter()
            setupfilter.set_name("GoG installer")
            setupfilter.add_pattern("setup_*.exe")
            chooser = gtk.FileChooserDialog(title="Setup executable",
                                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_OPEN,
                                                     gtk.RESPONSE_OK))
            chooser.set_default_response(gtk.RESPONSE_OK)
            chooser.add_filter(setupfilter)
            resp = chooser.run()
            if resp == gtk.RESPONSE_OK:
                setup_file = chooser.get_filename()
                chooser.destroy()
            else:
                chooser.destroy()
                return
        chooser = gtk.FileChooserDialog(title="Install root directory",
                                        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL,
                                                 gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        # Create default install path if it doesn't exist
        if not os.path.exists(self.settings.data["install_path"]):
            os.makedirs(self.settings.data["install_path"])
        chooser.set_current_folder(self.settings.data["install_path"])
        chooser.set_default_response(gtk.RESPONSE_OK)
        resp = chooser.run()
        if resp == gtk.RESPONSE_OK:
            path = chooser.get_filename()
            ExternalOutputWindow(self, self.selected_game, True, path,
                                 setup_file, self.have_beta_access == "True")
        chooser.destroy()

    def launchbutton_activated(self, widget):
        """
        Function called when the launch button has been clicked, we know
        the game is from the installed games list because else we couldn't
        have clicked the launch button.
        """
        game = self.database.games[self.selected_game]
        # Here we launch startgame.sh, the default startup element for all
        # games
        startup = os.path.join(game.install_path, "startgame.sh")
        subprocess.Popen([startup])

    # Same assumption as with the launch button. :)
    def uninstallbutton_activated(self, widget):
        """
        Function called when the uninstall button has been clicked, we know
        the game is from the installed games list because else we couldn't
        have clicked the uninstall button.
        """
        uninstall_message = ("You're about to uninstall %s, do you wish "
                             "to continue?" % self.selected_game)
        yesno = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                  gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                  uninstall_message)
        resp = yesno.run()
        yesno.destroy()
        if resp == gtk.RESPONSE_YES:
            ExternalOutputWindow(self, self.selected_game, False,
                                 beta=(self.have_beta_access == "True"))

    def limit_string(self, string, size):
        """
        Limit the size of the string cutting it at the beginning with ..
        """
        if len(string) <= size:
            return string
        else:
            return ".." + string[len(string) - size + 2:]

    def show_game_card(self, game, game_id=None):
        """
        Function that displays the game card menu for the relative game.
        If the game is currently installed, then it lets the user uninstall or
        launch it, else it lets the user install/download it.
        """
        if game_id in self.database.games:
            found_game = self.database.games[game_id]
            self.uninstallbutton.set_sensitive(True)
            self.installbutton.set_sensitive(False)
            self.launchbutton.set_sensitive(True)
            if self.database.games[game_id].launch_script == "404":
                self.launchbutton.set_sensitive(False)
            install_path = self.limit_string(found_game.install_path, 30)
            self.gameinstalledlabel.set_text(install_path)
            game_repo = self.limit_string(found_game.repo_url, 30)
            self.gamerepositorylabel.set_text(game_repo)
        else:
            self.uninstallbutton.set_sensitive(False)
            self.installbutton.set_sensitive(True)
            self.launchbutton.set_sensitive(False)
            self.gameinstalledlabel.set_text("Not Installed")
            self.gamerepositorylabel.set_text("Not Installed")
        self.selected_game = game_id
        self.gamenamelabel.set_text(game["title"])
        self.gameemulationlabel.set_text(game["emulation"])
        thread = threading.Thread(target=self.do_set_cover_image,
                                  args=(self.gamecoverimage, game["cover_url"]))
        thread.start()

    def check_for_updates(self, widget):
        """
        Check for updates on launcher scripts for each installed game and prompt
        the user to select which update he wants to install.
        """
        gamelist = {}
        model = self.installedgamestree.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            id = model.get_value(iter, 3)
            iter = model.iter_next(iter)
            gamelist[id] = self.database.games[id]
        if not gamelist:  # In case it's empty
            self.show_error("There are no games installed.")
            return
        UpdateWindow(gamelist)

    def key_pressed(self, widget, data):
        """ Function hooked to key pressing for the whole window. """
        if data.keyval == gtk.keysyms.Escape:
            self.rightpanel.hide()

    def do_login(self, widget):
        """ Spawn the login window asking for user credentials. """
        self.loginwindow = LoginWindow(self)

    def do_logout(self, widget):
        """ Disconnect the user and remove all the cookies from the pc. """
        settings_changed = False
        if "token" in self.settings.data:
            settings_changed = True
            del(self.settings.data["token"])
        if "secret" in self.settings.data:
            settings_changed = True
            del(self.settings.data["key"])
        self.islogged = False
        self.loginmenu.set_sensitive(True)
        self.logoutmenu.set_sensitive(False)
        self.window.set_title("%s - Offline Mode" % self.window_base_title)
        self.profiletabpage.hide()
        if settings_changed == True:
            self.settings.store()

    def login_callback(self):
        """ Function called when the login thread has been executed. """
        # We logged in successfully
        if self.loginwindow.result == "Success":
            if self.loginwindow.remember:
                self.settings.data["token"] = self.connection.auth_token.key
                self.settings.data["key"] = self.connection.auth_token.secret
                self.settings.store()
            self.loginwindow.loginglade.get_widget("logindialog").destroy()
            self.logged_successfully()
        # We closed the login dialog without logging in
        elif self.loginwindow.result == "Destroy":
            logindialog = self.loginwindow.loginglade.get_widget("logindialog")
            logindialog.destroy()
        # We failed the login process
        else:
            okbutton = self.loginwindow.loginglade.get_widget("okbutton")
            okbutton.set_sensitive(True)
            self.show_error(self.loginwindow.result)

    def logged_successfully(self):
        """ Set all the required parameters for a successful login. """
        self.islogged = True
        self.loginmenu.set_sensitive(False)
        self.logoutmenu.set_sensitive(True)
        self.profiletabpage.hide()
        self.do_profile_update()

    def do_profile_update(self):
        """
        Wrapper for threaded profile update call
        """
        thread = threading.Thread(target=self.__threaded_profile_update)
        thread.start()

    def __threaded_profile_update(self):
        """ 
        Threaded profile update
        """
        error = False
        data = None
        try:
            data = data_handle.UserData(self.connection.get_user_data())
        except:
            error = True
        gobject.idle_add(self.profile_update, data, error)


    def profile_update(self, data, error):
        """
        Function called through a timer, update profile and all
        related data on the GUI.
        """
        self.user = data
        if error:
            self.show_error("There was a connection problem with the login "
                            "page. Live profile update will be disabled.\n"
                            "Please relog/restart the client.")
            return False
        if not self.islogged:
            return False
        self.accountlabel.set_text(self.user.name)
        self.emaillabel.set_text(self.user.email)
        title = "%s - Logged in as: %s" % (self.window_base_title,
                                           self.user.name)
        self.window.set_title(title)
        if self.user.forum != "0":
            self.forumnotelabel.set_text(self.user.forum)
        else:
            self.forumnotelabel.set_text("none")
        if self.user.messages != "0":
            self.privatenotelabel.set_text(self.user.messages)
        else:
            self.privatenotelabel.set_text("none")
        if self.user.games != "0":
            self.gamenotelabel.set_text(self.user.games)
        else:
            self.gamenotelabel.set_text("none")
        # Let's load the picture from the web
        response = urllib2.urlopen(self.user.imagesmall)
        loader = gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()
        pixbuf = loader.get_pixbuf()
        self.profilepic.set_from_pixbuf(pixbuf.scale_simple(35, 35,
                                                            gtk.gdk.INTERP_BILINEAR))
        self.profiletabpage.show()
        # Refresh the update based on the settings
        # we do this because they may change dynamically
        # so we have to break the chain and re-create it every time
        gobject.timeout_add_seconds(int(self.settings.data["profile_update"]),
                                    self.do_profile_update)
        return False

    def show_error(self, error):
        """ Show an error message through a gtk message dialog. """
        dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, error)
        dialog.run()
        dialog.destroy()

    def show_warning(self, warning):
        """ Show a warning message through a gtk message dialog. """
        dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, warning)
        dialog.run()
        dialog.destroy()

    def main(self):
        """ Main function where gtk main loop is run. """
        gtk.main()

    def acquire_settings(self):
        """ Acquire settings from the settings class. """
        path = os.path.join(os.getenv("HOME"), ".gog-tux")
        self.settings = gog_settings.GogSettings(path)

    def save_settings(self, widget):
        """
        Save local settings changed on the GUI onto the filesystem by
        storing them into the settings class.
        """
        virtual_desktop = str(self.virtualdesktopcheck.get_active())
        virtual_resolution = self.virtualresentry.get_text()
        profile_update = self.profileintervalentry.get_text()
        access_beta = str(self.betasoftwarecheck.get_active())
        self.settings.data["install_path"] = self.installpathentry.get_text()
        self.settings.data["use_virtual_desktop"] = virtual_desktop
        self.settings.data["virtual_resolution"] = virtual_resolution
        self.settings.data["profile_update"] = profile_update
        self.settings.data["access_beta"] = access_beta
        self.settings.store()

    def undo_settings(self, widget):
        """ Revert the unmodified settings to their previous state. """
        self.installpathentry.set_text(self.settings.data["install_path"])
        virtual_desktop = self.settings.data["use_virtual_desktop"] == "True"
        self.virtualdesktopcheck.set_active(virtual_desktop)
        self.virtualresentry.set_text(self.settings.data["virtual_resolution"])
        profile_update = str(self.settings.data["profile_update"])
        self.profileintervalentry.set_text(profile_update)
        access_beta = self.settings.data["access_beta"] == "True"
        self.betasoftwarecheck.set_active(access_beta)

    def check_cookies(self):
        """ Check if the cookies are set in the settings or not. """
        if "token" in self.settings.data and "key" in self.settings.data:
            return True
        else:
            return False

    def obtain_cookies(self):
        """ Obtain the cookies from the settings. """
        return (self.settings.data["token"], self.settings.data["key"])

    def do_load_games(self, online=True):
        """
        Load game lists from the remote connection to gogonlinux or from the
        locally stored cache, and then call function to load local game list.
        """
        if not online and not os.path.exists(CACHE_PATH): 
            return
        beta = self.have_beta_access == "True"
        if not online:
            self.game_data = site_conn.obtain_available_games(beta, CACHE_PATH)
        else:
            self.game_data = site_conn.obtain_available_games(beta)
            with open(CACHE_PATH, "w") as f:
                f.write(json.dumps(self.game_data))
        self.availgameslist.clear()
        for name, content in self.game_data.items():
            if content["released"] == '0':
                image = self.beta
            else:
                image = self.compat[content["compat"]]
            self.availgameslist.append((content["title"], content["emulation"],
                                        image, name))
        self.refresh_local_list()

    def refresh_local_list(self):
        """ Refresh list of installed games by loading them from the db. """
        self.database.update()
        self.installedgameslist.clear()
        for game_id, game in self.database.games.items():
            # TODO: Check if the game has been released in the meantime or not
            if game.released == '0':
                if self.have_beta_access != "True":
                    continue
                image = self.beta
            else:
                image = self.compat[game.compat]
            self.installedgameslist.append((game.full_name, game.emulation,
                                            image, game_id))
        self.installedgamestree.get_selection().unselect_all()
        self.availablegamestree.get_selection().unselect_all()
        self.rightpanel.hide()

    def do_set_cover_image(self, gui, url):
        """ Set cover image from the given remote url for said game. """
        response = urllib2.urlopen(url)
        loader = gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()
        gui.set_from_pixbuf(loader.get_pixbuf())

    def load_games(self):
        """ Load list of available games from gogonlinux.com (threaded) """
        thread = threading.Thread(target=self.do_load_games)
        thread.start()


class LoginWindow:
    """ Class representing the GUI of the Login window. """

    def __init__(self, parent):
        self.loginglade = gtk.glade.XML(os.path.join(PACKAGE_DIRECTORY,
                                                     "login.glade"))
        loginwin = self.loginglade.get_widget("logindialog")
        signals = {"on_cancelbutton_clicked": self.close,
                   "on_logindialog_close": self.close,
                   "on_okbutton_clicked": self.do_login,
                   "on_passwordtext_activated": self.do_login,
                   "on_emailtext_activated": self.do_login}
        loginwin.connect("delete-event", self.close)
        self.loginglade.signal_autoconnect(signals)
        loginwin.show()
        self.parent = parent

    def close(self, widget):
        """ Close the login window. """
        self.result = "Destroy"
        self.parent.login_callback()

    def do_login(self, widget):
        """ Execute the login process (threaded). """
        email = self.loginglade.get_widget("emailtext").get_text().strip()
        password = self.loginglade.get_widget(
            "passwordtext").get_text().strip()
        remembercheckbox = self.loginglade.get_widget("remembercheckbox")
        self.remember = remembercheckbox.get_active()
        if not email or not password:
            self.parent.show_error("Please fill in all the fields")
            return
        self.loginglade.get_widget("okbutton").set_sensitive(False)
        thread = threading.Thread(target=self.__threaded_do_login,
                                  args=(email, password))
        thread.start()

    def __threaded_do_login(self, email, password):
        """ Thread instance that handles the login process. """
        try:
            self.parent.connection.connect(email, password)
            self.result = "Success"
        except Exception, exception:
            self.result = "%s" % exception
        gobject.idle_add(self.parent.login_callback)


class ExternalOutputWindow:
    """
    Class that handles the GUI and methods used to interact with an
    external CLI command.
    """
    working = True
    process = None

    def __init__(self, parent, game_id, install=True, path=None,
                 installer=None, beta=False):
        self.glade = gtk.glade.XML(os.path.join(PACKAGE_DIRECTORY,
                                   "externalwindow.glade"))
        self.window = self.glade.get_widget("externalwindow")
        self.window.set_icon(ICON)
        self.textview = self.glade.get_widget("outputview")
        self.textview.modify_base(gtk.STATE_NORMAL,
                                  gtk.gdk.color_parse('black'))
        self.textview.modify_text(gtk.STATE_NORMAL,
                                  gtk.gdk.color_parse('green'))
        self.spinner = self.glade.get_widget("spinner1")
        self.buf = gtk.TextBuffer()
        self.textview.set_buffer(self.buf)
        signals = {"on_action_activated": self.do_action}
        self.button = self.glade.get_widget("okbutton")
        self.button.set_label("Cancel")
        self.glade.signal_autoconnect(signals)
        self.window.show()
        self.parent = parent
        self.install_mode = install
        self.game_id = game_id
        self.path = path
        if install:
            self.window.set_title("Installing %s" % game_id)
            self.launch_install(game_id, path, installer, beta)
        else:
            self.window.set_title("Uninstalling %s" % game_id)
            self.button.set_label("Ok")
            self.button.set_sensitive(False)
            self.launch_uninstall(game_id, beta)

    def read_output(self, source, condition):
        """ Read the output from the cli command and output it to GUI. """
        if condition == gobject.IO_IN:
            try:
                char = source.read(1)
                self.buf.insert_at_cursor(char)
                self.textview.scroll_to_mark(self.buf.get_insert(), 0)
                return True
            except:
                return False
        else:
            # Let's give the chance to flush the buffer just in case
            self.buf.insert_at_cursor(source.read(4096))
            return False

    def __threaded_execute(self, command):  
        """ Thread instance that executes a cli command. """
        self.working = True
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        gobject.io_add_watch(self.process.stdout,
                             gobject.IO_IN | gobject.IO_HUP, self.read_output)
        gobject.io_add_watch(self.process.stderr,
                             gobject.IO_IN | gobject.IO_HUP, self.read_output)
        self.process.wait()
        self.stop_working()

    def stop_working(self):
        """ Stop the working process, setting the relevant data properly. """
        self.working = False
        self.button.set_label("Ok")
        self.button.set_sensitive(True)
        self.spinner.stop()

    def launch_install(self, game_id, path, installer, beta):
        """ Launch the command required to install a game through cli. """
        # If possible, I'd love this to be more elegant but so far it works
        cmd = "gog-installer "
        if beta:
            cmd += "--beta "
        if path != None:
            cmd += ("--install-path=%s " % os.path.join(path, game_id))
        if installer != None:
            cmd += (" --setup=%s" % installer)
        else:
            token = self.parent.connection.auth_token.key
            secret = self.parent.connection.auth_token.secret
            cmd += ("--secret=%s --token=%s" % (secret, token))
        cmd += " %s" % game_id
        self.thread = threading.Thread(target=self.__threaded_execute,
                                       args=([cmd.split()]))
        self.thread.start()

    def launch_uninstall(self, game_id, beta):
        """ Launc the command required to uninstall a game through cli. """
        if beta:
            beta_string = "--beta "
        else:
            beta_string = ""
        cmd = ("gog-installer %s -u %s" % (beta_string, game_id))
        thread = threading.Thread(target=self.__threaded_execute,
                                  args=([cmd.split()]))
        thread.start()

    def cleanup(self):
        """ Perform necessary cleanup functions. """
        self.parent.refresh_local_list()
        self.window.destroy()

    def do_action(self, widget):
        """ React to the click of the only active button in the window. """
        if self.working:  # If we need to cancel the action
            if not self.install_mode:  # we cannot cancel an uninstall, sadly
                return
            self.process.send_signal(signal.SIGINT)
        else:  # if we are done
            self.cleanup()


class UpdateWindow:
    """
    This class shows a windows with a list of updateable installed games and
    asks the user to update them or not.
    """

    games = None
    window = None
    gladeFile = None
    selected = None
    statusbox = None
    statusspinner = None
    messagelabel = None
    done = False
    selectedcount = 0

    def __init__(self, gamelist):
        if gamelist is None:
            raise Exception("You need at least one game to update.")
        self.games = gamelist
        self.gladeFile = gtk.glade.XML(os.path.join(PACKAGE_DIRECTORY,
                                       "updatewindow.glade"))
        signals = {"on_cancelbutton_activated": self.close_window,
                   "on_okbutton_activated": self.run_update}
        self.gladeFile.signal_autoconnect(signals)
        self.window = self.gladeFile.get_widget("updatewindow")
        self.statusbox = self.gladeFile.get_widget("statusbox")
        self.statusspinner = self.gladeFile.get_widget("statusspinner")
        self.messagelabel = self.gladeFile.get_widget("messagelabel")
        self.statusbox.hide()
        self.create_list_data()
        self.window.show()

    def create_list_data(self):
        """ Adds elements to the listview tree. """
        updatelisttree = self.gladeFile.get_widget("updatelisttree")
        textrenderer = gtk.CellRendererText()
        togglerenderer = gtk.CellRendererToggle()
        columna = gtk.TreeViewColumn("Games", textrenderer, text=0)
        columnb = gtk.TreeViewColumn("Update", togglerenderer, active=1)
        self.selected = gtk.ListStore(gobject.TYPE_STRING,
                                      gobject.TYPE_BOOLEAN,
                                      gobject.TYPE_STRING)
        updatelisttree.append_column(columna)
        updatelisttree.append_column(columnb)
        self.selected.set_sort_column_id(0, gtk.SORT_ASCENDING)
        updatelisttree.set_model(self.selected)
        togglerenderer.connect("toggled", self.__toggled, updatelisttree)
        for item in self.games:
            if (self.games[item].private == '1'):
                continue  # We don't support updates for private repos yet
            self.selected.append((self.games[item].full_name, False,
                                  self.games[item].online_id))

    def __toggled(self, toggle, path, *ignore):
        """ Signal connected to the action of toggling the update checkbox. """
        iter = self.selected.get_iter(path)
        value = self.selected.get_value(iter, 1)
        if value:
            self.selectedcount -= 1
        else:
            self.selectedcount += 1
        self.selected.set_value(iter, 1, not value)

    def close_window(self, widget):
        """ Signal triggered when cancel button is clicked. """
        self.window.destroy()

    def __threaded_update(self):
        """ Manage the connection and checking for updates in a thread. """
        iter = self.selected.get_iter_first()
        data = site_conn.obtain_launch_md5_list()
        while iter is not None:
            if self.selected.get_value(iter, 1) is True:
                gameid = self.selected.get_value(iter, 2)
                gamemd5 = self.games[gameid].obtain_launcher_md5()
                if data[gameid]["md5"] != gamemd5:
                    msg = ("%s has outdated launcher.\n"
                           "Updating launcher script..." %
                           self.games[gameid].full_name)

                    self.update_status(msg)
                    path = self.games[gameid].install_path
                    launch_script = os.path.join(path, "startgame.sh")
                    site_conn.download_script(launch_script,
                                              data[gameid]["url"])
            iter = self.selected.iter_next(iter)
        self.update_status("Update successful.")
        self.statusspinner.stop()
        self.done = True
        okbutton = self.gladeFile.get_widget("okbutton")
        okbutton.set_sensitive(True)
        okbutton.set_label("Done")

    def run_update(self, widget):
        """ Signal triggered when the ok button is clicked. """
        if self.done or self.selectedcount == 0:
            self.close_window(None)
            return
        self.statusbox.show()
        self.statusspinner.start()
        cancelbutton = self.gladeFile.get_widget("cancelbutton")
        cancelbutton.set_sensitive(False)
        okbutton = self.gladeFile.get_widget("okbutton")
        okbutton.set_sensitive(False)
        self.update_status("Performing update...")
        thread = threading.Thread(target=self.__threaded_update)
        thread.start()

    def update_status(self, message):
        """ Print a status message in the messagelabel on screen. """
        self.messagelabel.set_text(message)
