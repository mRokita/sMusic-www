#-*- coding: utf-8 -*-
from flask import request, render_template, redirect, Response, stream_with_context
import json
import re
from urllib import urlopen

from shared import app, db
from access_control import admin_perm, library_browse_perm, music_control_perm, upload_perm
import access_control
import config
import radio_utils
import upload
from __init__ import __version__

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

app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
app.secret_key = config.secret_key


@app.context_processor
def inject_is_admin():
    navigation_bar = [('/', 'index', u'Odtwarzacz'),
                      ('/library/', 'library', u'Biblioteka'),
                      ('/upload/', 'upload', u'Dodawanie utworów'),
                      ('/admin/', 'admin', u'Administracja')]
    return dict(is_admin=admin_perm.can(), can_upload=upload_perm.can(), navigation_bar=navigation_bar)


@app.before_first_request
def create_default_user():
    db.create_all()
    access_control.fill_database()
    db.session.commit()


def fix_chars(string):
    for char in CHAR_FIX:
        string = string.replace(char, CHAR_FIX[char])
    return string


def render_template_with_args(template, **kwargs):
    return render_template(template, radio_utils=radio_utils, version=__version__, **kwargs)


@app.route('/')
def ui_player():
    return render_template_with_args("player.html")


@app.route('/library/')
@library_browse_perm.require(http_exception=403)
def ui_library():
    return render_template_with_args("library_artists.html")


@app.route('/search/')
@library_browse_perm.require(http_exception=403)
def ui_library_search():
    query = request.args["q"]
    return render_template_with_args("library_search.html", query=query)


@app.route('/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist(artist):
    return render_template_with_args("library_artist_albums.html", artist=artist)


@app.route('/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist_album(artist, album):
    return render_template_with_args("library_artist_album_tracks.html", artist=artist, album=album)


@app.route('/api/v1/library/')
@library_browse_perm.require(http_exception=403)
def api_v1_library():
    return json.dumps(radio_utils.get_artists())


@app.route('/api/v1/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist(artist):
    return json.dumps(radio_utils.get_albums(artist))


@app.route('/api/v1/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist_album(artist, album):
    return json.dumps(radio_utils.get_tracks(artist, album))


@app.route('/api/v1/play_next/')
@music_control_perm.require(http_exception=403)
def api_v1_play_next():
    return json.dumps(radio_utils.play_next())


@app.route('/api/v1/play_prev/')
@music_control_perm.require(http_exception=403)
def api_v1_play_prev():
    return json.dumps(radio_utils.play_prev())


@app.route('/api/v1/pause/')
@music_control_perm.require(http_exception=403)
def api_v1_pause():
    return json.dumps(radio_utils.pause())


@app.route('/api/v1/vol/<value>/')
@music_control_perm.require(http_exception=403)
def api_v1_vol(value):
    return json.dumps(radio_utils.set_vol(value))


@app.route('/api/v1/seek/<position>/')
@music_control_perm.require(http_exception=403)
def api_v1_seek(position):
    return json.dumps(radio_utils.seek(position))

@app.route('/api/v1/status/')
def api_v1_status():
    return json.dumps(radio_utils.get_status())


@app.route('/api/v1/clear_q_and_play/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_q_and_play(artist_id, album_id, track_id):
    return json.dumps(radio_utils.clear_queue_and_play(artist_id, album_id, track_id))


@app.route('/api/v1/clear_queue/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_queue():
    return json.dumps(radio_utils.clear_queue())


@app.route('/api/v1/add_to_q/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_add_to_q(artist_id, album_id, track_id):
    return json.dumps(radio_utils.add_to_queue(artist_id, album_id, track_id))


@app.route('/api/v1/current_queue/')
def api_v1_current_queue():
    return json.dumps(radio_utils.get_current_queue())


@app.route('/api/v1/search_track/<query>')
@library_browse_perm.require(http_exception=403)
def api_v1_search_track(query):
    return json.dumps(radio_utils.search_for_track(query))


@app.route('/api/v1/albumart/<artist>/<album>/')
def api_v1_album_art(artist, album):
    url = ALBUM_ART_URL.format(unicode(fix_chars(artist).encode("utf-8")),
                               PATTERN_FIX_ALBUM.sub("", unicode(fix_chars(album).encode("utf-8"))))
    return Response(stream_with_context(urlopen(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0])))


@app.route('/api/v1/play/')
@music_control_perm.require(http_exception=403)
def play():
    return json.dumps(radio_utils.play())

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")
