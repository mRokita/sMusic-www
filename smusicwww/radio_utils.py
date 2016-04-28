import socket
import ssl
import json
from base64 import b64encode, b64decode

import config
from __init__ import __version__
import logs


def escape(msg):
    return b64encode(msg)+"\n"


def un_escape(msg):
    return b64decode(msg)


def send_for_result(dct):
    timeout = 2
    if dct["request"] in ["get_artists", "get_tracks", "get_albums"]:
        timeout = 6
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(escape(json.dumps(dct)), ("localhost", 3485))
    buff = ""
    while len(buff) == 0 or not buff[-1] == "\n":
        data, server = sock.recvfrom(4096)
        buff += data
    return json.loads(b64decode(buff[:-1]))


def get_artists():
    return send_for_result({"request": "get_artists"})


def get_albums(artist=None):
    return send_for_result({"request": "get_albums", "artist": artist})


def search_for_track(query):
    return send_for_result({"request": "search_for_track", "query": query})


def clear_queue():
    return send_for_result({"request": "clear_queue"})


def clear_queue_and_play(artist_id, album_id, track_id):
    return send_for_result({"request": "set_queue_to_single_track", "artist_id": artist_id, "album_id": album_id, "track_id": track_id, "start_playing": True})


def add_to_queue(artist_id, album_id, track_id):
    return send_for_result({"request": "add_to_queue", "artist_id": artist_id, "album_id": album_id, "track_id": track_id})


def get_tracks(artist=None, album=None):
    return send_for_result({"request": "get_tracks", "artist": artist, "album": album})


def get_current_queue():
    return send_for_result({"request": "get_current_queue"})


def get_status():
    return send_for_result({"request": "status"})


def set_vol(value):
    return send_for_result({"request": "set_vol", "value": value})

def seek(position):
    return send_for_result({"request": "seek", "position": position})

def play_prev():
    return send_for_result({"request": "play_prev"})


def play_next():
    return send_for_result({"request": "play_next"})


def play():
    return send_for_result({"request": "play"})


def pause():
    return send_for_result({"request": "pause"})


def add_download(method, url, artist=None, album=None, track=None):
    to_send = {"request": "add_download", "url": method+";"+url}
    if artist is not None:
        to_send["artist"] = artist
    if album is not None:
        to_send["album"] = album
    if track is not None:
        to_send["track"] = track
    return send_for_result(to_send)


def get_current_dowanlod_queue():
    return send_for_result({"request": "get_download_queue"})


def clear_download_queue():
    return send_for_result({"request": "clear_download_queue"})


def download_status():
    return send_for_result({"request": "download_status"})
