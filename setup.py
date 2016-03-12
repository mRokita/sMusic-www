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

data = ['smusicwww/static/js/main.js',
        'smusicwww/static/materialize/js/materialize.min.js',
        'smusicwww/static/materialize/js/materialize.js', 'smusicwww/static/materialize/LICENSE',
        'smusicwww/static/materialize/font/roboto/Roboto-Medium.woff2',
        'smusicwww/static/materialize/font/roboto/Roboto-Regular.ttf',
        'smusicwww/static/materialize/font/roboto/Roboto-Medium.eot',
        'smusicwww/static/materialize/font/roboto/Roboto-Thin.eot',
        'smusicwww/static/materialize/font/roboto/Roboto-Thin.woff2',
        'smusicwww/static/materialize/font/roboto/Roboto-Bold.woff2',
        'smusicwww/static/materialize/font/roboto/Roboto-Regular.woff',
        'smusicwww/static/materialize/font/roboto/Roboto-Bold.woff',
        'smusicwww/static/materialize/font/roboto/Roboto-Thin.ttf',
        'smusicwww/static/materialize/font/roboto/Roboto-Light.woff',
        'smusicwww/static/materialize/font/roboto/Roboto-Regular.woff2',
        'smusicwww/static/materialize/font/roboto/Roboto-Regular.eot',
        'smusicwww/static/materialize/font/roboto/Roboto-Medium.woff',
        'smusicwww/static/materialize/font/roboto/Roboto-Thin.woff',
        'smusicwww/static/materialize/font/roboto/Roboto-Light.woff2',
        'smusicwww/static/materialize/font/roboto/Roboto-Bold.eot',
        'smusicwww/static/materialize/font/roboto/Roboto-Light.ttf',
        'smusicwww/static/materialize/font/roboto/Roboto-Medium.ttf',
        'smusicwww/static/materialize/font/roboto/Roboto-Light.eot',
        'smusicwww/static/materialize/font/roboto/Roboto-Bold.ttf',
        'smusicwww/static/materialize/font/material-design-icons/LICENSE.txt',
        'smusicwww/static/materialize/font/material-design-icons/Material-Design-Icons.svg',
        'smusicwww/static/materialize/font/material-design-icons/Material-Design-Icons.ttf',
        'smusicwww/static/materialize/font/material-design-icons/Material-Design-Icons.eot',
        'smusicwww/static/materialize/font/material-design-icons/Material-Design-Icons.woff2',
        'smusicwww/static/materialize/font/material-design-icons/Material-Design-Icons.woff',
        'smusicwww/static/materialize/README.md',
        'smusicwww/static/materialize/css/materialize.css',
        'smusicwww/static/materialize/css/materialize.min.css',
        'smusicwww/static/nouislider.css',
        'smusicwww/static/nouislider.pips.css',
        'smusicwww/static/nouislider.js',
        'smusicwww/static/nouislider.min.js',
        'smusicwww/static/nouislider.min.css',
        'smusicwww/static/nouislider.tooltips.css',
        'smusicwww/static/css/style.css',
        'smusicwww/templates/base.html',
        'smusicwww/templates/library_artists.html',
        'smusicwww/templates/library_search.html',
        'smusicwww/templates/player.html',
        'smusicwww/templates/library_artist_album_tracks.html',
        'smusicwww/templates/library_artist_albums.html',
        'smusicwww/templates/library.html',
        'smusicwww/templates/search_box.html']

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
