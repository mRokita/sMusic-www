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
    return json.loads(b64decode(buff[:-1]))


def play():
    send_for_result({"request": "play"})


def pause():
    send_for_result({"request": "pause"})