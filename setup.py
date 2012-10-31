# -*- mode: python; coding: utf-8 -*-

from distutils.core import setup

def get_changelog_version():
    with file('debian/changelog') as chlog:
        return chlog.readline().split()[1][1:-1]

setup(name = 'EasyXBee',
      version = get_changelog_version(),
      author = "Oscar Aceña",
      author_email = "oscaracena@gmail.com",
      url = "https://bitbucket.org/OscarAcena/easyxbee/overview",

      package_dir = {"": "src"},
      py_modules = ['EasyXBee'],
      )

