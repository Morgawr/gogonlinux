#!/usr/bin/env python

import sys
import os
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import gtk.glade
import threading
import time

version = "0.1.0"
author = "Morgawr"
email = "morgawr@gmail.com"
package_directory = os.path.dirname(os.path.abspath(__file__))
gobject.threads_init()

class GogTuxGUI:
    
    def __init__(self, connection):
        self.connection = connection
        self.gladefile = os.path.join(package_directory,"gog_tux.glade")
        self.wTree = gtk.glade.XML(self.gladefile)
        self.rightpanel = self.wTree.get_widget("fixed1")
        self.rightpanel.hide()
        
        #This is a dictionary of all the signals handled by our GUI
        signals = { "on_gog_tux_destroy" : gtk.main_quit,
                    "on_close_menu_activated" : gtk.main_quit,
                    "on_about_menu_activated" : self.about_menu_activated }

        self.wTree.signal_autoconnect(signals)

        self.window = self.wTree.get_widget("gog_tux")
        self.window.show()
        self.loginwindow = LoginWindow(self)

    
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
    
    def login_callback(self):
        if self.loginwindow.result == "Success": #we logged in successfully
            self.loginwindow.loginglade.get_widget("logindialog").destroy()
        else: #we failed the login process
            self.loginwindow.loginglade.get_widget("okbutton").set_sensitive(True)
            self.show_error(self.loginwindow.result)
           

    def show_error(self, error):
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                               gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, error)
        md.run()
        md.destroy()

    def main(self):
        gtk.main()

class LoginWindow:

    def __init__(self, parent):
        self.loginglade = gtk.glade.XML(os.path.join(package_directory,"login.glade"))
        loginwin = self.loginglade.get_widget("logindialog")
        signals = { "on_cancelbutton_activated" : gtk.main_quit,
                    "on_cancelbutton_clicked" : gtk.main_quit,
                    "on_logindialog_close" : gtk.main_quit,
                    "on_okbutton_activated" : self.do_login,
                    "on_okbutton_clicked" : self.do_login }
        self.loginglade.signal_autoconnect(signals)
        loginwin.show()
        self.parent = parent
 
    def do_login(self, widget):
        email = self.loginglade.get_widget("emailtext").get_text().strip()
        password = self.loginglade.get_widget("passwordtext").get_text().strip()
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
   

