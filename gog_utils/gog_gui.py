
import sys
import os
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import gtk.glade
import threading
import time
import data_handle
import urllib2
import ConfigParser
import subprocess
import shutil

import gog_db
import gol_connection as site_conn
from version import version
from version import author
from version import email

package_directory = os.path.dirname(os.path.abspath(__file__))
dbpath = os.path.join(os.getenv("HOME"), ".gog-tux", "db.json")
gobject.threads_init()

class GogTuxGUI:
    
    #some image data
    compat = {}
    compat["green"] = gtk.gdk.pixbuf_new_from_file(os.path.join(package_directory,"imgdata","green_compat.png"))
    compat["yellow"] = gtk.gdk.pixbuf_new_from_file(os.path.join(package_directory,"imgdata","yellow_compat.png"))
    compat["red"] = gtk.gdk.pixbuf_new_from_file(os.path.join(package_directory,"imgdata","red_compat.png"))
    beta = gtk.gdk.pixbuf_new_from_file(os.path.join(package_directory,"imgdata","beta.png"))
    icon = gtk.gdk.pixbuf_new_from_file(os.path.join(package_directory,"imgdata","gog-tux-icon.svg"))

    #some other default stuff
    islogged = False
    game_data = {} # list of all available games from the website
    selected_game = None

    window_base_title = "(unofficial) Gog Linux Client"


    def __init__(self, connection):
        self.connection = connection
        self.gladefile = os.path.join(package_directory,"gog_tux.glade")
        self.wTree = gtk.glade.XML(self.gladefile)
        self.rightpanel = self.wTree.get_widget("fixed1")
        self.rightpanel.hide()
        if not os.path.exists(os.path.join(os.getenv("HOME"), ".gog-tux")):
            os.makedirs(os.path.join(os.getenv("HOME"),".gog-tux"))
        self.database = gog_db.GogDatabase(dbpath)
        #This is a dictionary of all the signals handled by our GUI
        signals = { "on_gog_tux_destroy" : gtk.main_quit,
                    "on_close_menu_activated" : gtk.main_quit,
                    "on_about_menu_activated" : self.about_menu_activated,
                    "on_undoprefsbutton_clicked" : self.undo_settings,
                    "on_saveprefsbutton_clicked" : self.save_settings,
                    "on_gog_tux_key_pressed" : self.key_pressed,
                    "on_installbutton_activated" : self.installbutton_activated,
                    "on_launchbutton_activated" : self.launchbutton_activated,
                    "on_uninstallbutton_activated" : self.uninstallbutton_activated,
                    "on_logoutmenu_activated" : self.do_logout,
                    "on_loginmenu_activated" : self.do_login }
        self.wTree.signal_autoconnect(signals)
        #obtain required resources
        self.window = self.wTree.get_widget("gog_tux")
        #set up gui elements
        self.init_gui_elements()
        #set up the lists for the games 
        self.init_lists()
        #finalize initialization
        self.acquire_settings()
        self.have_beta_access = self.settings["access_beta"]
        self.load_games()
        if self.check_cookies():
            token, key = self.obtain_cookies()
            self.connection.set_auth_token(token, key)
            self.logged_successfully()
        else:
            self.do_logout(None)
        self.window.show()
        self.undo_settings(None)

    # Performs initialization of some gui elements storing them in the class
    def init_gui_elements(self):
        self.accountlabel = self.wTree.get_widget("accountlabel")
        self.emaillabel = self.wTree.get_widget("emaillabel")
        self.gamenotelabel = self.wTree.get_widget("gamenotelabel")
        self.forumnotelabel = self.wTree.get_widget("forumnotelabel")
        self.privatenotelabel = self.wTree.get_widget("privatenotelabel")
        self.profilepic = self.wTree.get_widget("profilepic")
        self.installpathentry = self.wTree.get_widget("installpathentry")
        self.virtualresentry = self.wTree.get_widget("resolutionentry")
        self.virtualdesktopcheck = self.wTree.get_widget("virtualdesktopcheck")
        self.betasoftwarecheck = self.wTree.get_widget("betasoftwarecheck")
        self.profileintervalentry = self.wTree.get_widget("profileintervalentry")
        self.launchbutton = self.wTree.get_widget("launchbutton")
        self.installbutton = self.wTree.get_widget("installbutton")
        self.uninstallbutton = self.wTree.get_widget("uninstallbutton")
        self.gamenamelabel = self.wTree.get_widget("namelabel")
        self.gameinstalledlabel = self.wTree.get_widget("installedlabel")
        self.gameemulationlabel = self.wTree.get_widget("emulationlabel")
        self.gamecoverimage = self.wTree.get_widget("coverimage")
        self.loginmenu = self.wTree.get_widget("loginmenu")
        self.logoutmenu = self.wTree.get_widget("logoutmenu")
        self.profiletablabel = self.wTree.get_widget("profiletablabel")
        self.profiletabpage = self.wTree.get_widget("profiletabpage")
        self.window.set_icon(self.icon)
        
    # Performs initialization of the available and installed games lists
    def init_lists(self):
        self.availablegamestree = self.wTree.get_widget("availablegamestree")
        self.installedgamestree = self.wTree.get_widget("installedgamestree")
        textrenderer = gtk.CellRendererText()
        imagerenderer = gtk.CellRendererPixbuf()
        columna = gtk.TreeViewColumn("Games", textrenderer, text=0)
        columnb = gtk.TreeViewColumn("Emulation mode", textrenderer, text=1)
        columnc = gtk.TreeViewColumn("Compatibility", imagerenderer)
        columnc.add_attribute(imagerenderer,"pixbuf", 2)
        inst_columna = gtk.TreeViewColumn("Games", textrenderer, text=0)
        inst_columnb = gtk.TreeViewColumn("Emulation mode", textrenderer, text=1)
        inst_columnc = gtk.TreeViewColumn("Compatibility", imagerenderer)
        inst_columnc.add_attribute(imagerenderer,"pixbuf", 2)
        
        # setup list of available games and installed games
        # 0 is the displayed name
        # 1 is emulation mode
        # 2 is visual representation of current compatibility state (green, yellow and red)
        # 3 is the game id in the lookup dictionary, not going to be displayed, just used for retrieval
        self.availgameslist = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_STRING)
        self.installedgameslist = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_STRING)
        self.availgameslist.set_sort_column_id(0,gtk.SORT_ASCENDING)
        self.installedgameslist.set_sort_column_id(0,gtk.SORT_ASCENDING)
        self.availablegamestree.set_model(self.availgameslist)
        self.availablegamestree.append_column(columna)
        self.availablegamestree.append_column(columnb)
        self.availablegamestree.append_column(columnc)
        self.installedgamestree.set_model(self.installedgameslist)
        self.installedgamestree.append_column(inst_columna)
        self.installedgamestree.append_column(inst_columnb)
        self.installedgamestree.append_column(inst_columnc)
        selection = self.availablegamestree.get_selection()
        selection.connect("changed", self.list_selection_changed, self.availablegamestree)
        selection = self.installedgamestree.get_selection()
        selection.connect("changed", self.list_selection_changed, self.installedgamestree)

    # This simply creates the about popup window and appends relevant data
    def about_menu_activated(self, widget, data=None):
        about = gtk.AboutDialog()
        about.set_program_name("Gog Linux Client")
        about.set_version(version)
        about.set_copyright(author+" - "+email)
        about.set_comments("Unofficial Linux client for the gog.com platform")
        about.set_website("http://www.gogonlinux.com")
        about.run()
        about.destroy()

    # Signal that reacts to either available games or installed games has been clicked
    def list_selection_changed(self, widget, data):
        if data == self.availablegamestree or data == self.installedgamestree:
            self.rightpanel.show()
            items, paths = data.get_selection().get_selected_rows()
            element = items.get_iter(paths[0])
            game = self.game_data[items.get_value(element,3)]
            self.show_game_card(game,items.get_value(element,3))
        else:
            self.rightpanel.hide()

    # We know the selected game is from the available games list
    # because it's not installed yet, else this button would be
    # disabled
    def installbutton_activated(self, widget, data=None):
        if self.game_data[self.selected_game]["message"] != None:
            self.show_warning(self.game_data[self.selected_game]["message"])
        setup_file = None
        if self.islogged == True:
            yesno = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                                      gtk.BUTTONS_YES_NO, "Do you want to use an already downloaded setup file?")
            resp = yesno.run()
            yesno.destroy()
        if self.islogged == False or resp == gtk.RESPONSE_YES:
            # we need to create a filter for the .exe files so we don't choose a wrong file
            setupfilter = gtk.FileFilter()
            setupfilter.set_name("GoG installer")
            setupfilter.add_pattern("setup_*.exe")
            chooser = gtk.FileChooserDialog(title="Setup executable", action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            chooser.set_default_response(gtk.RESPONSE_OK)
            chooser.add_filter(setupfilter)
            resp = chooser.run()
            if resp == gtk.RESPONSE_OK:
                setup_file = chooser.get_filename()
                chooser.destroy()
            else:
                chooser.destroy()
                return
        chooser = gtk.FileChooserDialog(title="Install directory", action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_current_folder(self.settings["install_path"])
        chooser.set_current_name(self.selected_game)
        chooser.set_default_response(gtk.RESPONSE_OK)
        resp = chooser.run()
        if resp == gtk.RESPONSE_OK:
            path = chooser.get_filename()
            installwindow = ExternalOutputWindow(self,self.selected_game, True, path, setup_file, self.have_beta_access == "True")
        chooser.destroy()

    # We know the selected game is from the installed games list
    # else you wouldn't be able to launch it.
    def launchbutton_activated(self, widget, data=None):
        game = self.database.games[self.selected_game]
        # Here we launch startgame.sh which is the default startup element for all games
        startup = os.path.join(game.install_path,"startgame.sh")
        subprocess.Popen([startup])

    # Same assumption as with the launch button. :)
    def uninstallbutton_activated(self, widget, data=None):
        yesno = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                                  gtk.BUTTONS_YES_NO, ("You're about to uninstall %s do you wish to continue?" % self.selected_game))
        resp = yesno.run()
        yesno.destroy()
        if resp == gtk.RESPONSE_YES:        
            uninstallwindow = ExternalOutputWindow(self, self.selected_game, False, beta=(self.have_beta_access == "True"))

    # Shows the game card of the selected game. 
    # If the game is currently installed then it lets the user uninstall it or launch it
    # If the game is not installed it lets the user download it
    def show_game_card(self, game, game_id=None):
        if game_id in self.database.games.keys():
            self.uninstallbutton.set_sensitive(True)
            self.installbutton.set_sensitive(False)
            self.launchbutton.set_sensitive(True)
            self.gameinstalledlabel.set_text(self.database.games[game_id].install_path)
        else:
            self.uninstallbutton.set_sensitive(False)
            self.installbutton.set_sensitive(True)
            self.launchbutton.set_sensitive(False)
            self.gameinstalledlabel.set_text("Not Installed")
        self.selected_game = game_id
        self.gamenamelabel.set_text(game["title"])
        self.gameemulationlabel.set_text(game["emulation"])
        t = threading.Thread(target=self.do_set_cover_image, args=(self.gamecoverimage, game["cover_url"]))
        t.start()

    def key_pressed(self, widget, data):
        if data.keyval == gtk.keysyms.Escape:
            self.rightpanel.hide()

    def do_login(self, widget):
        self.loginwindow = LoginWindow(self)

    def do_logout(self, widget):
        settings_changed = False
        if "token" in self.settings.keys():
            settings_changed = True
            del(self.settings["token"])
        if "secret" in self.settings.keys():
            settings_changed = True
            del(self.settings["key"])
        self.islogged = False
        self.loginmenu.set_sensitive(True)
        self.logoutmenu.set_sensitive(False)
        self.window.set_title("%s - Offline Mode" % self.window_base_title)
        self.profiletabpage.hide()
        if settings_changed == True:
            self.store_settings()
    
    def login_callback(self):
        if self.loginwindow.result == "Success": #we logged in successfully
            if self.loginwindow.remember:
                self.settings["token"] = self.connection.auth_token.key
                self.settings["key"] = self.connection.auth_token.secret
                self.store_settings()
            self.loginwindow.loginglade.get_widget("logindialog").destroy()
            self.logged_successfully()
        elif self.loginwindow.result == "Destroy": #we close the login dialog without logging in
            self.loginwindow.loginglade.get_widget("logindialog").destroy()
        else: #we failed the login process
            self.loginwindow.loginglade.get_widget("okbutton").set_sensitive(True)
            self.show_error(self.loginwindow.result)

    def logged_successfully(self):
        self.islogged = True
        self.loginmenu.set_sensitive(False)
        self.logoutmenu.set_sensitive(True)
        self.profiletabpage.show()
        self.profile_update()

    def profile_update(self):
        try:
            self.user = data_handle.UserData(self.connection.get_user_data())
        except:
            self.show_error("There was a connection problem with the login page. Live profile update will be disabled.\n"
                            "Please relog/restart the client.")
            return False

        if not self.islogged:
            return False
        self.accountlabel.set_text(self.user.name)
        self.emaillabel.set_text(self.user.email)
        self.window.set_title(self.window_base_title+" - Logged in as: "+self.user.name)
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
        #Let's load the picture from the web
        response = urllib2.urlopen(self.user.imagesmall)
        loader = gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()
        self.profilepic.set_from_pixbuf(loader.get_pixbuf().scale_simple(35,35,gtk.gdk.INTERP_BILINEAR))
        #refresh the update based on the settings, we do this because they may change dynamically
        #so we have to break the chain and re-create it every time
        gobject.timeout_add_seconds(int(self.settings["profile_update"]),self.profile_update)
        return False


    def show_error(self, error):
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                               gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, error)
        md.run()
        md.destroy()

    def show_warning(self, warning):
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                               gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, warning)
        md.run()
        md.destroy()

    def main(self):
        gtk.main()

    def acquire_settings(self):
        path = os.path.join(os.getenv("HOME"),".gog-tux")
        if not os.path.exists(path):
            os.makedirs(path)
        configfile = os.path.join(path,"config")
        if not os.path.exists(configfile):
            self.settings = self.obtain_default_settings()
            self.store_settings()
        else:
            self.settings = self.load_settings(configfile)

    #difference between this and store_settings is that this function 
    #obtains the settings from the GUI, applies them to the program
    #and only then calls store_settings to update the settings
    #on the filesystem
    def save_settings(self, widget):
        self.settings["install_path"] = self.installpathentry.get_text()
        self.settings["use_virtual_desktop"] = str(self.virtualdesktopcheck.get_active())
        self.settings["virtual_resolution"] = self.virtualresentry.get_text()
        self.settings["profile_update"] = self.profileintervalentry.get_text()
        self.settings["access_beta"] = str(self.betasoftwarecheck.get_active())
        self.store_settings()

    #we revert to the unmodified settings
    def undo_settings(self, widget):
        self.installpathentry.set_text(self.settings["install_path"])
        self.virtualdesktopcheck.set_active(self.settings["use_virtual_desktop"] == "True")
        self.virtualresentry.set_text(self.settings["virtual_resolution"])
        self.profileintervalentry.set_text(str(self.settings["profile_update"]))
        self.betasoftwarecheck.set_active(self.settings["access_beta"] == "True")

    def store_settings(self):
        path = os.path.join(os.getenv("HOME"),".gog-tux")
        if not os.path.exists(path):
            os.makedirs(path)
        configfile = os.path.join(path,"config")
        parser = ConfigParser.ConfigParser()
        section = "settings"
        parser.add_section(section)
        parser.set(section,"install_path", self.settings["install_path"])
        parser.set(section,"use_virtual_desktop", self.settings["use_virtual_desktop"])
        parser.set(section,"virtual_resolution", self.settings["virtual_resolution"])
        parser.set(section,"profile_update", self.settings["profile_update"])
        parser.set(section,"access_beta", self.settings["access_beta"])
        if "token" in self.settings and "key" in self.settings:
            parser.set(section,"token", self.settings["token"])
            parser.set(section,"key", self.settings["key"])
        f = open(configfile,'w+')
        parser.write(f)
        f.close()

    def check_cookies(self):
        if "token" in self.settings and "key" in self.settings:
            return True
        else:
            return False

    def obtain_cookies(self):
        return (self.settings["token"], self.settings["key"])

    def obtain_default_settings(self):
        sets = {}
        sets["install_path"] = os.path.join(os.getenv("HOME"),"games","gog")
        sets["use_virtual_desktop"] = False
        sets["profile_update"] = 120
        sets["virtual_resolution"] = "800x600"
        sets["access_beta"] = False
        return sets

    def load_settings(self, conf):
        parser = ConfigParser.ConfigParser()
        parser.read(conf)
        sets = {}
        section = "settings"
        for opt in parser.options(section):
            try:
                sets[opt] = parser.get(section, opt)
            except:
                print "Exception in config parsing on %s " % option
                sets[opt] = None
        return sets

    def do_load_games(self):
        if self.have_beta_access == "True":
            self.game_data = site_conn.obtain_beta_available_games()
        else:
            self.game_data = site_conn.obtain_available_games()
        for name, content in self.game_data.items():
            if content["released"] == '0':
                image = self.beta
            else:
                image = self.compat[content["compat"]]
            self.availgameslist.append((content["title"],content["emulation"],image,name))
        self.refresh_local_list()
    
    def refresh_local_list(self):
        self.database.update()
        self.installedgameslist.clear()
        for game_id, game in self.database.games.items():
            if game.released == '0':
                if self.have_beta_access != "True":
                    continue
                image = self.beta
            else:
                image = self.compat[game.compat]
            self.installedgameslist.append((game.full_name, game.emulation, image, game_id))
        self.installedgamestree.get_selection().unselect_all()
        self.availablegamestree.get_selection().unselect_all()
        self.rightpanel.hide()

    def do_set_cover_image(self, gui, url):
        response = urllib2.urlopen(url)
        loader = gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()
        gui.set_from_pixbuf(loader.get_pixbuf())

    #loads the list of available games from gogonlinux.com
    def load_games(self):
        t = threading.Thread(target=self.do_load_games)
        t.start()


class LoginWindow:

    def __init__(self, parent):
        self.loginglade = gtk.glade.XML(os.path.join(package_directory, "login.glade"))
        loginwin = self.loginglade.get_widget("logindialog")
        signals = { "on_cancelbutton_clicked" : self.close,
                    "on_logindialog_close" : self.close,
                    "on_okbutton_clicked" : self.do_login,
                    "on_passwordtext_activated" : self.do_login,
                    "on_emailtext_activated" : self.do_login }
        loginwin.connect("delete-event", self.close)
        self.loginglade.signal_autoconnect(signals)
        loginwin.show()
        self.parent = parent

    def close(self, widget, data=None):
        self.result = "Destroy"
        self.parent.login_callback()
 
    def do_login(self, widget):
        email = self.loginglade.get_widget("emailtext").get_text().strip()
        password = self.loginglade.get_widget("passwordtext").get_text().strip()
        self.remember = self.loginglade.get_widget("remembercheckbox").get_active()
        if not email or not password:
            self.parent.show_error("Please fill in all the fields")
            return
        self.loginglade.get_widget("okbutton").set_sensitive(False)
        t = threading.Thread(target=self.__threaded_do_login, args=(email, password))
        t.start()
              
    def __threaded_do_login(self, email, password):
        try:
            self.parent.connection.connect(email, password)
            self.result = "Success"
        except Exception, e:
            self.result = "%s" % e
        gobject.idle_add(self.parent.login_callback)
   

class ExternalOutputWindow:

    working = True
    process = None
    
    def __init__(self, parent, game_id, install=True, path=None, installer=None, beta=False):
        self.glade = gtk.glade.XML(os.path.join(package_directory, "externalwindow.glade"))
        self.window = self.glade.get_widget("externalwindow")
        self.textview = self.glade.get_widget("outputview")
        self.textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
        self.textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('green'))
        self.spinner = self.glade.get_widget("spinner1")
        self.buf = gtk.TextBuffer()
        self.textview.set_buffer(self.buf)
        signals = { "on_action_activated" : self.do_action }
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
        if condition == gobject.IO_IN:
            try:
                char = source.read(1)
                self.buf.insert_at_cursor(char)
                self.textview.scroll_to_mark(self.buf.get_insert(), 0)
                return True
            except:
                return False
        else:
            return False

    def __threaded_execute(self, command, pipe):
        self.working = True
        gobject.io_add_watch(pipe.stdout, gobject.IO_IN | gobject.IO_HUP, self.read_output)
        pipe.stdin.write(command)
        pipe.stdin.flush()
        pipe.wait()
        pipe.stdin.close()
        if pipe.returncode == 3: # This means we failed to fetch an installer from gog.com
            self.buf.insert_at_cursor("You do not have the permission required to install this game.")
        self.working = False
        self.button.set_label("Ok")
        self.button.set_sensitive(True)
        self.spinner.stop()

    def launch_install(self, game_id, path, installer, beta):
        self.process = command = subprocess.Popen(["sh"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # If possible, I'd love this to be more elegant but so far it works
        cmd = "gog-installer "
        if beta:
            cmd += "--beta "
        if path != None:
            cmd += ("--install-path=%s " % path)
        if installer != None:
            cmd += (" --setup=%s" % installer)
        else:
            token = self.parent.connection.auth_token.key
            secret = self.parent.connection.auth_token.secret
            cmd += ("--secret=%s --token=%s" % (secret,token))
        cmd += " "+game_id+"\nexit\n"
        thread = threading.Thread(target=self.__threaded_execute, args=(cmd, command))
        thread.start()

    def launch_uninstall(self, game_id, beta):
        if beta:
            beta_string = "--beta "
        else:
            beta_string = ""
        self.process = command = subprocess.Popen(["sh"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        cmd = ("gog-installer %s -u %s\nexit\n" % (beta_string, game_id))
        thread = threading.Thread(target=self.__threaded_execute, args=(cmd, command))
        thread.start()

    def cleanup(self):
        self.parent.refresh_local_list()
        self.window.destroy()

    def stop_install(self):
        shutil.rmtree(self.path)  
        #ExternalOutputWindow(self.parent, self.game_id, False)
        self.cleanup()

    def do_action(self, widget, data=None):
        if self.working: # If we need to cancel the action
            if not self.install_mode: # we cannot cancel an uninstall, sadly
                return
            self.process.kill()
            self.cleanup()
            self.stop_install()
        else: # if we are done
            self.cleanup()

