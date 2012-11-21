#!/usr/bin/env python
from distutils.core import setup
from gog_utils import version as ver

setup(name='gogonlinux',
      version=ver.version,
      description='Client for GOG games on Linux',
      author=ver.author,
      author_email=ver.email,
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
