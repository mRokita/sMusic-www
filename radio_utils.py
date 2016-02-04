import socket
import ssl
import config
import json
from base64 import b64encode, b64decode


def escape(msg):
    return b64encode(msg)+"\n"


def un_escape(msg):
    return b64decode(msg)


def send_for_result(dct):
    conn = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    conn.connect(("127.0.0.1", config.listen_port))
    conn.read()
    conn.send(escape(json.dumps({"request": "ok", "type": "www", "key": "a"})))
    conn.send(escape(json.dumps(dct)))
    buff = ""
    while len(buff) == 0 or not buff[-1] == "\n":
        buff += conn.read()
    conn.close()
    return json.loads(b64decode(buff[:-1]))


def get_artists():
    return send_for_result({"request": "get_artists"})


def get_albums(artist=None):
    return send_for_result({"request": "get_albums", "artist": artist})


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


def play_prev():
    return send_for_result({"request": "play_prev"})


def play_next():
    return send_for_result({"request": "play_next"})



def play():
    return send_for_result({"request": "play"})


def pause():
    return send_for_result({"request": "pause"})

