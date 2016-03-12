#!/usr/bin/python2
# -*- coding: utf-8 -*-

from distutils.core import setup
from smusicwww import __version__
from os import listdir
from os.path import isdir, join


def recursive_paths(dir):
    paths = []
    for f in listdir(dir):
        if isdir(join(dir, f)):
            paths.extend(recursive_paths(join(dir, f)))
        else:
            paths.append(join(dir, f))

    return paths

data = []
data.extend(recursive_paths("smusicwww/static"))
data.extend(recursive_paths("smusicwww/templates"))

setup(name="sMusicServer",
      version=__version__,
      description="Serwer sMusic",
      url="https://github.com/mRokita/sMusic-www/",
      download_url="https://github.com/mRokita/sMusic-www/tarball/%s" % __version__,
      keywords=["smusic", "www", "server", "serwer", "staszic", "music"],
      author="Michał Rokita & Artur Puzio",
      author_email="mrokita@mrokita.pl & cytadela88@gmail.com",
      packages=["smusicwww"],
      package_data={
        'smusicwww': data
      },
      scripts=["sMusicServer"],
      requires=["flask", "jinja2"],
      data_files=[('/etc/sMusic/', ['server.default.ini']),
                  ('/usr/share/sMusic/', ['smusicwww.wsgi']),
                  ('/usr/lib/systemd/system', ['sMusicServer.service'])],
      )
