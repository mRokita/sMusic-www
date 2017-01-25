# -*- coding: utf-8 -*-
from flask import request, render_template, redirect, current_app, url_for
from werkzeug.routing import RequestRedirect
import flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, \
    fresh_login_required, login_fresh
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, \
    UserNeed, Permission, TypeNeed
from flask_admin import Admin, AdminIndexView
import flask_admin
from flask_admin.contrib import sqla
from passlib.apps import custom_app_context as pwd_context

from shared import app, db
from utils import get_or_create, secure_random_string_generator
from access_control import radio_change_perm
import access_control
import config
import json
import socket
import ssl
from base64 import b64encode, b64decode
import config
from __init__ import __version__


def escape(msg):
    return b64encode(msg) + "\n"


def un_escape(msg):
    return b64decode(msg)


def send_for_result(dct):
    conn = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    timeout = 2
    if dct["request"] in ["get_artists", "get_tracks", "get_albums", "get_current_queue", "get_playlist", "get_playlists"]:
        timeout = 10
    conn.settimeout(timeout)
    conn.connect(("127.0.0.1", config.listen_port))
    conn.read()
    conn.send(escape(json.dumps({"request": "ok", "type": "www", "version": __version__})))
    conn.send(escape(json.dumps(dct)))
    buff = ""
    while len(buff) == 0 or not buff[-1] == "\n":
        buff += conn.read()
    conn.close()
    return json.loads(b64decode(buff[:-1]))


class Radio(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    access_key = db.Column(db.String(32), unique=True)
    comment = db.Column(db.String(1024))
    column_display_pk = False
    users = db.relationship("User", back_populates="radio")
    last_seen = db.Column(db.DateTime())

    def generate_new_access_key(self):
        self.access_key = secure_random_string_generator(32)

    def __init__(self, name="none", access_key=""):
        self.name = name
        if access_key == "":
            self.generate_new_access_key()
        else:
            self.access_key = access_key

    def __str__(self):
        return "%s - %s" % (self.id, self.name)

    def send_request(self, dct):
        dct["radio"] = self.id
        return send_for_result(dct)

    def get_artists(self):
        return self.send_request({"request": "get_artists"})

    def get_albums(self, artist=None):
        return self.send_request({"request": "get_albums", "artist": artist})

    def search_for_track(self, query):
        return self.send_request({"request": "search_for_track", "query": query})

    def clear_queue(self):
        return self.send_request({"request": "clear_queue"})

    def clear_queue_and_play(self, artist_id, album_id, track_id):
        return self.send_request(
            {"request": "set_queue_to_single_track", "artist_id": artist_id, "album_id": album_id, "track_id": track_id,
             "start_playing": True})

    def del_track_from_playlist(self, playlist_id, track_num):
        return self.send_request({
            "request": "del_track_from_playlist", "playlist_id": playlist_id, "track_num": track_num
        })

    def add_to_queue(self, artist_id, album_id, track_id):
        return self.send_request(
            {"request": "add_to_queue", "artist_id": artist_id, "album_id": album_id, "track_id": track_id})

    def add_track_to_playlist(self, playlist_id, artist_id, album_id, track_id):
        return self.send_request({
            "request": "add_track_to_playlist", "playlist_id": playlist_id,
            "artist_id": artist_id, "album_id": album_id, "track_id": track_id})

    def create_playlist(self, playlist_name):
        return self.send_request({"request": "create_playlist", "playlist_name": playlist_name})

    def del_playlist(self, playlist_id):
        return self.send_request({"request": "del_playlist", "playlist_id": playlist_id})

    def add_playlist_to_queue(self, playlist_id):
        return self.send_request(
            {"request": "add_playlist_to_queue", "playlist_id": playlist_id})

    def clear_queue_and_play_playlist(self, playlist_id):
        return self.send_request(
            {"request": "set_queue_to_playlist", "start_playing": True, "playlist_id": playlist_id})

    def change_playlist_order(self, playlist_id, source_index, dest_index):
        return self.send_request({"request": "change_playlist_order", "playlist_id": playlist_id, "source_index": source_index, "dest_index": dest_index})

    def move_queue_item(self, source_index, dest_index):
        return self.send_request({"request": "move_queue_item", "source_index": source_index, "dest_index": dest_index})

    def set_queue_position(self, pos):
        return self.send_request({"request": "set_queue_position", "pos": pos})

    def del_from_queue(self, pos):
        return self.send_request({"request": "del_from_queue", "pos": pos})

    def get_playlist(self, playlist_id):
        return self.send_request({"request": "get_playlist", "playlist_id": playlist_id})

    def get_playlists(self):
        return self.send_request({"request": "get_playlists"})

    def get_tracks(self, artist=None, album=None):
        return self.send_request({"request": "get_tracks", "artist": artist, "album": album})

    def get_current_queue(self):
        return self.send_request({"request": "get_current_queue"})

    def get_status(self):
        return self.send_request({"request": "status"})

    def set_vol(self, value):
        return self.send_request({"request": "set_vol", "value": value})

    def seek(self, position):
        return self.send_request({"request": "seek", "position": position})

    def play_prev(self):
        return self.send_request({"request": "play_prev"})

    def play_next(self):
        return self.send_request({"request": "play_next"})

    def play(self):
        return self.send_request({"request": "play"})

    def pause(self):
        return self.send_request({"request": "pause"})

    def toggle_mode(self):
        return self.send_request({"request": "toggle_mode"})

    def add_download(self, method, url, artist=None, album=None, track=None):
        to_send = {"request": "add_download", "url": method + ";" + url}
        if artist is not None:
            to_send["artist"] = artist
        if album is not None:
            to_send["album"] = album
        if track is not None:
            to_send["track"] = track
        return self.send_request(to_send)

    def get_current_download_queue(self):
        return self.send_request({"request": "get_download_queue"})

    def clear_download_queue(self):
        return self.send_request({"request": "clear_download_queue"})

    def download_status(self):
        return self.send_request({"request": "download_status"})

    def is_connected(self):
        return self.id in connected_radios_ids()


def connected_radios_ids():
    return send_for_result({"request": "list_connected", "radio": -1})["radios_list"]


def connected_radios():
    radios_ids = connected_radios_ids()
    if len(radios_ids) > 0:
        return Radio.query.filter(Radio.id.in_(radios_ids)).all()
    else:
        return []


@app.route('/api/v1/change_radio/<radio_id>')
@radio_change_perm.require(http_exception=403)
def self_change_radio(radio_id):
    radio = Radio.query.get(radio_id)
    if radio is not None:
        current_user.radio = radio
        db.session.add(current_user)
        db.session.commit()
        return json.dumps({"type": "ok"})
    else:
        return json.dumps({"type": "error", "subtype": "wrong_id", "message": "Radio o podanym ID nie istnieje"})
