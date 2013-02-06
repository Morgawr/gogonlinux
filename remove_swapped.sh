#!/bin/bash

# This script is just for gogonlinux developers who edit GUI files, 
# the outdated version of glade creates an unrecognized attribute which is
# swapped="no". This in turns creates no problems for the application but 
# prints a lot of text to the terminal and can be annoying for the end-user.

# Launch the script only when you modify .glade files and find out that the 
# GUI application is printing out such trash warnings.

find gog_utils -name *.glade | xargs sed -i "s/swapped=\"no\"//g" 
