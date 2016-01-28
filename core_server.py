"""
Bardzo minimalny testowy serwer TCP
"""
import socket
import ssl
import config
from base64 import b64decode, b64encode
import json
import re
from inspect import getargspec
from threading import Thread
from functools import partial

msgid = 0
binds = {}
queries = {}
radio = None
PATTERN_MSG = re.compile("([ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=+/]*?)\n(.+)?", re.DOTALL)


def bind(function):
    argspec = getargspec(function)
    print argspec
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
    return b64encode(msg)+"\n"


def un_escape(msg):
    return b64decode(msg)


@bind
def ok(conn, type, key):
    if type=="radio" and key=="jasfdljLWAUFEDJSDnqld":
        radio = conn


def handle_client(conn, addr):
    global msgid
    conn.write(escape(json.dumps({"request": "type"})))
    msg = conn.read()
    buff = ""
    while msg:
        parsed_msg = PATTERN_MSG.findall(msg)
        print parsed_msg
        if len(parsed_msg) == 1 and len(parsed_msg[0]) == 2:
            buff += parsed_msg[0][1]
            esc_string = parsed_msg[0][0]
            try:
                data = json.loads(un_escape(esc_string))
                print data
                if "request" in data:
                    if conn != radio and radio:
                        msgid += 1
                        ret["msgid"] = msgid
                        queries[msgid] = conn
                        radio.write(escape(json.dumps(ret)))
                    elif conn == radio and not "msgid" in data:
                        target = binds[data["request"]]["target"]
                        msgid = None
                        if "msgid" in data:
                            msgid = binds[data["msgid"]]
                        del data["request"]
                        del data["msgid"]
                        ret = target(conn, addr, **data)
                        if msgid:
                            ret["msgid"] = msgid
                        conn.send(escape(json.dumps(ret)))
                    elif conn == radio and "msgid" in data:
                        c = queries[data["msgid"]]
                        del data["msgid"]
                        c.write(escape(json.dumps(ret)))
            except ValueError:
                pass

        else:
            buff = ""
        msg = conn.read()
    print "end"


def main():
    bind_socket = socket.socket()
    bind_socket.bind(('localhost', config.listen_port))
    bind_socket.listen(5)
    try:
        while True:
            new_socket, from_addr = bind_socket.accept()
            print from_addr
            conn = ssl.wrap_socket(new_socket,
                                   server_side=True,
                                   certfile=config.ssl_cert_file,
                                   keyfile=config.ssl_key_file)

            Thread(target=partial(handle_client, conn, from_addr)).start()

    except KeyboardInterrupt:
        bind_socket.close()


if __name__ == "__main__":
    main()
