#!/usr/bin/env python
from distutils.core import setup

setup(name='gog-tux',
      version='0.1.0',
      description='Client for GOG games on Linux',
      author='Morgawr',
      author_email='morgawr@gmail.com',
      url='www.gogonlinux.com',
      packages=['gog_utils'],
      scripts=['gog-tux']
      )
