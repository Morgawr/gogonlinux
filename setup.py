#!/usr/bin/env python
from distutils.core import setup

setup(name='gogonlinux',
      version='0.1.3',
      description='Client for GOG games on Linux',
      author='Morgawr',
      author_email='morgawr@gmail.com',
      license='3-clause BSD',
      url='www.gogonlinux.com',
      packages=['gog_utils'],
      package_dir={'gog_utils' : 'gog_utils'},
      package_data={'gog_utils' : ['imgdata/*','*.glade']},
      scripts=['gog-tux','gog-installer'],
      long_description=("This a linux porting attempt for gog.com games. It offers compatibility patches "
                        "and an easy to setup and install/uninstall package for all gog games. "
                        "A gog account is required."),
      platforms=['GNU/Linux']
      )
