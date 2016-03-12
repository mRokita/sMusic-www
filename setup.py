#!/usr/bin/python2
# -*- coding: utf-8 -*-

from distutils.core import setup
from smusicwww import __version__

setup(name="sMusicServer",
      version=__version__,
      description="Serwer sMusic",
      url="https://github.com/mRokita/sMusic-www/",
      download_url="https://github.com/mRokita/sMusic-www/tarball/%s" % __version__,
      keywords=["smusic", "www", "server", "serwer", "staszic", "music"],
      author="Michał Rokita & Artur Puzio",
      author_email="mrokita@mrokita.pl & cytadela88@gmail.com",
      packages=["smusicwww"],
      include_package_data=True,
      scripts=["sMusicServer"],
      requires=["flask", "jinja2"],
      data_files=[('/etc/sMusic/', ['server.default.ini']),
                  ('/usr/share/sMusic/', ['smusicwww.wsgi']),
                  ('/usr/lib/systemd/system', ['sMusicServer.service'])],
      )
