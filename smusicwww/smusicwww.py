#-*- coding: utf-8 -*-
from __future__ import print_function
from functools import wraps
from flask import request, Response, Flask, render_template, redirect
import json
import re
from urllib import urlopen

from __init__ import config, radio_utils

app = Flask(__name__)
__version__ = "0.1.1 Alpha"
ALBUM_ART_URL = "http://www.slothradio.com/covers/?adv=0&artist={}&album={}"
PATTERN_ALBUM_ART = re.compile("\\<div class\\=\\\"album0\\\"\\>\\<img src\\=\\\"(.*?)\\\"")
PATTERN_FIX_ALBUM = re.compile("( ?\\(.*?\\))|(\\ ?[Dd][Ii][Ss][Cc] \d)|(\\ ?[Cc][Dd] \d)|(\\&)|(\\,)|( UK)|( US)")
CHAR_FIX = {u"ó": u"o",
            u"ź": u"z",
            u"ł": u"l",
            u"ą": u"a",
            u"ś": u"s",
            u"ć": u"c",
            u"ę": u"e",
            u"ń": u"n"}


def fix_chars(string):
    for char in CHAR_FIX:
        string = string.replace(char, CHAR_FIX[char])
    return string


def check_auth():
    """
    Ta funkcja sprawdza, czy dane logowania są prawidłowe
    """
    auth = request.authorization
    return auth and auth.username == config.admin_login and auth.password == config.admin_password


def render_template_with_args(template, **kwargs):
    return render_template(template, radio_utils=radio_utils, version=__version__, **kwargs)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def ui_player():
    return render_template_with_args("player.html", is_logged_in = check_auth())


@app.route('/login/')
def ui_login():
    return authenticate()


@app.route('/library/')
@requires_auth
def ui_library():
    return render_template_with_args("library_artists.html")


@app.route('/search/')
@requires_auth
def ui_library_search():
    query = request.args["q"]
    return render_template_with_args("library_search.html", query=query)


@app.route('/library/<artist>/')
@requires_auth
def ui_library_artist(artist):
    return render_template_with_args("library_artist_albums.html", artist=artist)


@app.route('/library/<artist>/<album>/')
@requires_auth
def ui_library_artist_album(artist, album):
    return render_template_with_args("library_artist_album_tracks.html", artist=artist, album=album)


@app.route('/api/v1/library/')
@requires_auth
def api_v1_library():
    return json.dumps(radio_utils.get_artists())


@app.route('/api/v1/library/<artist>/')
@requires_auth
def api_v1_library_artist(artist):
    return json.dumps(radio_utils.get_albums(artist))


@app.route('/api/v1/library/<artist>/<album>/')
@requires_auth
def api_v1_library_artist_album(artist, album):
    return json.dumps(radio_utils.get_tracks(artist, album))


@app.route('/api/v1/play_next/')
@requires_auth
def api_v1_play_next():
    return json.dumps(radio_utils.play_next())


@app.route('/api/v1/play_prev/')
@requires_auth
def api_v1_play_prev():
    return json.dumps(radio_utils.play_prev())


@app.route('/api/v1/pause/')
@requires_auth
def api_v1_pause():
    return json.dumps(radio_utils.pause())


@app.route('/api/v1/vol/<value>/')
@requires_auth
def api_v1_vol(value):
    return json.dumps(radio_utils.set_vol(value))


@app.route('/api/v1/status/')
def api_v1_status():
    return json.dumps(radio_utils.get_status())


@app.route('/api/v1/clear_q_and_play/<artist_id>/<album_id>/<track_id>/')
@requires_auth
def api_v1_clear_q_and_play(artist_id, album_id, track_id):
    return json.dumps(radio_utils.clear_queue_and_play(artist_id, album_id, track_id))


@app.route('/api/v1/clear_queue/')
@requires_auth
def api_v1_clear_queue():
    return json.dumps(radio_utils.clear_queue())


@app.route('/api/v1/add_to_q/<artist_id>/<album_id>/<track_id>/')
@requires_auth
def api_v1_add_to_q(artist_id, album_id, track_id):
    return json.dumps(radio_utils.add_to_queue(artist_id, album_id, track_id))


@app.route('/api/v1/current_queue/')
def api_v1_current_queue():
    return json.dumps(radio_utils.get_current_queue())


@app.route('/api/v1/search_track/<query>')
@requires_auth
def api_v1_search_track(query):
    return json.dumps(radio_utils.search_for_track(query))


@app.route('/api/v1/albumart/<artist>/<album>/')
def api_v1_album_art(artist, album):
    url = ALBUM_ART_URL.format(unicode(fix_chars(artist).encode("utf-8")), PATTERN_FIX_ALBUM.sub("", unicode(fix_chars(album).encode("utf-8"))))
    return redirect(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0], 302)


@app.route('/api/v1/play/')
@requires_auth
def play():
    return json.dumps(radio_utils.play())

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")
