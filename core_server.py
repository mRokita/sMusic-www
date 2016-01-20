"""
Bardzo minimalny testowy serwer TCP
"""
import socket
import ssl
import config
from base64 import b64decode, b64encode
import json
from threading import Thread
from functools import partial


def escape(msg):
    return b64encode(msg)+"\n"


def un_escape(msg):
    return b64decode(msg)


def handle_client(conn, addr):
    conn.write(escape('{"target":"print_to_console", "text": "hello world"}'))
    text = conn.read()
    while text:
        text = conn.read()
        try:
            data = json.loads(text)
        except ValueError:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            break
        print data


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
