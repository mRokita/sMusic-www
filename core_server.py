#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
Bardzo minimalny testowy serwer TCP
"""
import socket
import ssl
import config
from base64 import b64decode, b64encode
import json
import re
import sys
from inspect import getargspec
from threading import Thread
from functools import partial


__version__ = "0.1.0 Alpha"
msgid = 0
binds = {}
queries = {}
radio = None
PATTERN_MSG = re.compile("([ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=+/]*?)\n(.+)?", re.DOTALL)


def bind(function):
    argspec = getargspec(function)
    args = argspec[0]
    if argspec[-1]:
        req_args = args[:len(argspec[-1])-1]
    else:
        req_args = args
    binds[function.__name__] = {
        "target": function,
        "reqired_args": req_args,
        "args": args
    }
    return function


def escape(msg):
    return "\t"+b64encode(msg)+"\n"


def un_escape(msg):
    return b64decode(msg)


@bind
def ok(conn, addr, type, version, key=None):
    global radio
    if version != __version__:
        conn.send(escape(json.dumps({u"request": u"error",
                                     u"type": u"incompatibleVersions",
                                     u"cat": u"=^..^=",
                                     u"comment": u"Niekompatybilne wersje komponentow systemu."})))
        return False
    if type == "radio" and config.radio_key == key:
        radio = conn
        print "%s:%s został zarejestrowany jako RADIO" % addr
        return True
    if type == "www" and addr[0] == "127.0.0.1":
        print "%s:%s został zarejestrowany jako WWW" % addr
        return True
    return False


def handle_client(conn, addr):
    global msgid
    print "%s:%s połączył się" % addr
    is_registered = False
    conn.write(escape(json.dumps({"request": "type"})))
    msg = conn.read()
    buff = ""
    while msg:
        buff += msg
        print [buff]
        parsed_msg = PATTERN_MSG.findall(buff)
        print "msg: "+str(parsed_msg)
        if len(parsed_msg) == 1 and len(parsed_msg[0]) == 2:
            buff = parsed_msg[0][1]
            esc_string = parsed_msg[0][0]
            try:
                data = json.loads(un_escape(esc_string))
                print "%s:%s: %s" % (addr[0], addr[1], data)
                if "request" in data:
                    if conn != radio and radio and is_registered:
                        msgid += 1
                        datacpy = dict(data)
                        datacpy["msgid"] = msgid
                        queries[msgid] = conn
                        radio.write(escape(json.dumps(datacpy)))
                    elif conn == radio and not "msgid" in data or\
                            (not is_registered and "request" in data and data["request"] == "ok"):
                        datacpy = dict(data)
                        target = binds[datacpy["request"]]["target"]
                        send_response = datacpy["request"] != "ok"
                        del datacpy["request"]
                        ret = target(conn, addr, **datacpy)
                        if send_response:
                            conn.send(escape(json.dumps(ret)))
                        else:
                            is_registered = ret
                    elif conn == radio and "msgid" in data:
                        datacpy = dict(data)
                        c = queries[datacpy["msgid"]]
                        del datacpy["msgid"]
                        c.write(escape(json.dumps(datacpy)))
            except ValueError as e:
                print [un_escape(esc_string)]
                print e

        msg = conn.read()
    conn.close()
    print "%s:%s rozłączył się" % addr


def main():
    bind_socket = socket.socket()
    bind_socket.bind((config.listen_host, config.listen_port))
    print "Nasłuchiwanie na {}:{}".format(config.listen_host, config.listen_port)
    bind_socket.listen(5)
    conns = []
    try:
        while True:
            new_socket, from_addr = bind_socket.accept()
            conn = ssl.wrap_socket(new_socket,
                                   server_side=True,
                                   certfile=config.ssl_cert_file,
                                   keyfile=config.ssl_key_file)
            conns.append(conn)
            Thread(target=partial(handle_client, conn, from_addr)).start()

    except KeyboardInterrupt:
        bind_socket.shutdown(socket.SHUT_RDWR)
        bind_socket.close()


if __name__ == "__main__":
    print "+---------------------------------------------+\n|"+\
          ("sMusic-www/core_server v{}".format(__version__).center(45, " "))+"|\n|"+\
          ("https://github.com/mRokita/sMusic-www").center(45, " ")+\
          "|\n+---------------------------------------------+\n"
    main()
