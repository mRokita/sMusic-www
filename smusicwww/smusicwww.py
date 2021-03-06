#-*- coding: utf-8 -*-
from flask import request, render_template, redirect, Response, stream_with_context
import json
import re
from urllib import urlopen

from shared import app, db
from access_control import admin_perm, library_browse_perm, music_control_perm, upload_perm, radio_change_perm
from radio_management import Radio
import access_control
import config
import upload
from __init__ import __version__
from flask_login import current_user

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
def inject_menu_data():
    navigation_bar = [('/', 'index', u'Odtwarzacz'),
                      ('/library/', 'library', u'Biblioteka'),
                      ('/playlists/', 'playlists', u'Playlisty')]
    if upload_perm.can():
        navigation_bar.append(('/upload/', 'upload', u'Dodawanie utworów'))
    if admin_perm.can():
        navigation_bar.append(('/admin/', 'admin', u'Administracja'))
    ret = dict(navigation_bar=navigation_bar, version=__version__)
    ret["radio_change_can"] = False
    ret["radios"] = [{"id": radio.id, "name": radio.name} for radio in Radio.query.all()]
    ret["radio_current_name"] = current_user.radio.name
    if radio_change_perm.can():
        ret["radio_change_can"] = True
    return ret


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
    return render_template(template, version=__version__, **kwargs)


@app.route('/')
def ui_player():
    return render_template("player.html")


@app.route('/playlists/')
@library_browse_perm.require(http_exception=403)
def ui_playlists():
    return render_template("playlists.html")


@app.route('/playlists/<playlist>/')
@library_browse_perm.require(http_exception=403)
def ui_playlist_view(playlist):
    return render_template("playlist_view.html", playlist_id = playlist)


@app.route('/library/')
@library_browse_perm.require(http_exception=403)
def ui_library():
    return render_template("library_artists.html")


@app.route('/search/')
@library_browse_perm.require(http_exception=403)
def ui_library_search():
    query = request.args["q"]
    return render_template("library_search.html", query=query)


@app.route('/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist(artist):
    return render_template("library_artist_albums.html", artist=artist)


@app.route('/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def ui_library_artist_album(artist, album):
    return render_template("library_artist_album_tracks.html", artist=artist, album=album)


@app.route('/api/v1/playlists/')
@library_browse_perm.require(http_exception=403)
def api_v1_playlists():
    return json.dumps(current_user.radio.get_playlists())


@app.route('/api/v1/playlists/<playlist>')
@library_browse_perm.require(http_exception=403)
def api_v1_playlist_view(playlist):
    return json.dumps(current_user.radio.get_playlist(playlist))


@app.route('/api/v1/library/')
@library_browse_perm.require(http_exception=403)
def api_v1_library():
    return json.dumps(current_user.radio.get_artists())


@app.route('/api/v1/library/<artist>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist(artist):
    return json.dumps(current_user.radio.get_albums(artist))


@app.route('/api/v1/library/<artist>/<album>/')
@library_browse_perm.require(http_exception=403)
def api_v1_library_artist_album(artist, album):
    return json.dumps(current_user.radio.get_tracks(artist, album))


@app.route('/api/v1/play_next/')
@music_control_perm.require(http_exception=403)
def api_v1_play_next():
    return json.dumps(current_user.radio.play_next())


@app.route('/api/v1/play_prev/')
@music_control_perm.require(http_exception=403)
def api_v1_play_prev():
    return json.dumps(current_user.radio.play_prev())


@app.route('/api/v1/pause/')
@music_control_perm.require(http_exception=403)
def api_v1_pause():
    return json.dumps(current_user.radio.pause())


@app.route('/api/v1/vol/<value>/')
@music_control_perm.require(http_exception=403)
def api_v1_vol(value):
    return json.dumps(current_user.radio.set_vol(value))


@app.route('/api/v1/seek/<position>/')
@music_control_perm.require(http_exception=403)
def api_v1_seek(position):
    return json.dumps(current_user.radio.seek(position))


@app.route('/api/v1/status/')
def api_v1_status():
    return json.dumps(current_user.radio.get_status())


@app.route('/api/v1/toggle_mode/')
@music_control_perm.require(http_exception=403)
def api_v1_toggle_mode():
    return json.dumps(current_user.radio.toggle_mode())


@app.route('/api/v1/clear_q_and_play/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_q_and_play(artist_id, album_id, track_id):
    return json.dumps(current_user.radio.clear_queue_and_play(artist_id, album_id, track_id))


@app.route('/api/v1/clear_q_and_play_playlist/<playlist_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_q_and_play_playlist(playlist_id):
    return json.dumps(current_user.radio.clear_queue_and_play_playlist(playlist_id))


@app.route('/api/v1/add_playlist_to_queue/<playlist_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_add_playlist_to_queue(playlist_id):
    return json.dumps(current_user.radio.add_playlist_to_queue(playlist_id))

@app.route('/api/v1/clear_queue/')
@music_control_perm.require(http_exception=403)
def api_v1_clear_queue():
    return json.dumps(current_user.radio.clear_queue())


@app.route('/api/v1/add_to_q/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_add_to_q(artist_id, album_id, track_id):
    return json.dumps(current_user.radio.add_to_queue(artist_id, album_id, track_id))


@app.route('/api/v1/add_track_to_playlist/<playlist_id>/<artist_id>/<album_id>/<track_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_add_track_to_playlist(playlist_id, artist_id, album_id, track_id):
    return json.dumps(current_user.radio.add_track_to_playlist(playlist_id, artist_id, album_id, track_id))


@app.route('/api/v1/del_track_from_playlist/<playlist_id>/<track_num>/')
@music_control_perm.require(http_exception=403)
def api_v1_del_track_from_playlist(playlist_id, track_num):
    return json.dumps(current_user.radio.del_track_from_playlist(playlist_id, track_num))

@app.route('/api/v1/change_playlist_order/<playlist_id>/<source_index>/<dest_index>/')
@music_control_perm.require(http_exception=403)
def api_v1_change_playlist_order(playlist_id, source_index, dest_index):
    return json.dumps(current_user.radio.change_playlist_order(playlist_id, source_index, dest_index))


@app.route('/api/v1/set_queue_position/<pos>/')
@music_control_perm.require(http_exception=403)
def api_v1_set_queue_position(pos):
    return json.dumps(current_user.radio.set_queue_position(pos))


@app.route('/api/v1/del_from_queue/<pos>/')
@music_control_perm.require(http_exception=403)
def api_v1_del_from_queue(pos):
    return json.dumps(current_user.radio.del_from_queue(pos))

@app.route('/api/v1/move_queue_item/<source_index>/<dest_index>/')
@music_control_perm.require(http_exception=403)
def api_v1_move_queue_item(source_index, dest_index):
    return json.dumps(current_user.radio.move_queue_item(source_index, dest_index))


@app.route('/api/v1/create_playlist/<playlist_name>/')
@music_control_perm.require(http_exception=403)
def api_v1_create_playlist(playlist_name):
    return json.dumps(current_user.radio.create_playlist(playlist_name))


@app.route('/api/v1/del_playlist/<playlist_id>/')
@music_control_perm.require(http_exception=403)
def api_v1_del_playlist(playlist_id):
    return json.dumps(current_user.radio.del_playlist(playlist_id))


@app.route('/api/v1/current_queue/')
def api_v1_current_queue():
    return json.dumps(current_user.radio.get_current_queue())


@app.route('/api/v1/search_track/<query>')
@library_browse_perm.require(http_exception=403)
def api_v1_search_track(query):
    return json.dumps(current_user.radio.search_for_track(query))


@app.route('/api/v1/albumart/<artist>/<album>/')
def api_v1_album_art(artist, album):
    url = ALBUM_ART_URL.format(unicode(fix_chars(artist).encode("utf-8")),
                               PATTERN_FIX_ALBUM.sub("", unicode(fix_chars(album).encode("utf-8"))))
    return Response(stream_with_context(urlopen(PATTERN_ALBUM_ART.findall(urlopen(url).read())[0])))


@app.route('/api/v1/play/')
@music_control_perm.require(http_exception=403)
def play():
    return json.dumps(current_user.radio.play())

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")
