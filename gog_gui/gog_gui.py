#!/usr/bin/env python

import sys
import os
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade

version = "0.1.0"
author = "Morgawr"
email = "morgawr@gmail.com"
package_directory = os.path.dirname(os.path.abspath(__file__))

class GogTuxGUI:
    
    def __init__(self):

        self.gladefile = os.path.join(package_directory,"gog_tux.glade")
        self.wTree = gtk.glade.XML(self.gladefile)
        self.rightpanel = self.wTree.get_widget("fixed1")
        self.rightpanel.hide()
        
        #This is a dictionary of all the signals handled by our GUI
        signals = { "on_gog_tux_destroy" : gtk.main_quit,
                    "on_about_menu_activated" : self.about_menu_activated }

        self.wTree.signal_autoconnect(signals)

        self.window = self.wTree.get_widget("gog_tux")
        self.window.show()
        
    def about_menu_activated(self, widget, data=None):
        aboutglade = gtk.glade.XML(os.path.join(package_directory,"about.glade"))
        aboutwin = aboutglade.get_widget("aboutpopup")
        titlelabel = aboutglade.get_widget("titlelabel")
        titlelabel.set_text(titlelabel.get_text()+version)
        authorlabel = aboutglade.get_widget("authorlabel")
        authorlabel.set_text(author + " - " + email)
        aboutwin.show()

    def main(self):
        gtk.main()
