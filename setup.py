#!/usr/bin/env python
from distutils.core import setup
execfile('gog_utils/version.py')

setup(name='gogonlinux',
      version=version,
      description='Client for GOG games on Linux',
      author=author,
      author_email=email,
      license='3-clause BSD',
      url='www.gogonlinux.com',
      packages=['gog_utils'],
      package_dir={'gog_utils' : 'gog_utils'},
      package_data={'gog_utils' : ['imgdata/*','*.glade']},
      scripts=['gog-tux','gog-installer'],
      long_description=("This a linux porting attempt for gog.com games. It offers compatibility patches "
                        "and an easy to setup and install/uninstall package for all gog games. "
                        "A gog account is required."),
      data_files=[('/usr/local/share/applications/',['data/gog-tux.desktop']),
                  ('/usr/local/share/icons/',['gog_utils/imgdata/gog-tux-icon.svg'])
                  ('/usr/local/man/man1/',['gog-installer.1'])],
      platforms=['GNU/Linux']
      )
