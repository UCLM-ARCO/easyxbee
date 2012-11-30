#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import argparse

from EasyXBee import LocalNode


class Discoverer:
    def __init__(self, device):
        self._device = device

        self.local = LocalNode(tty=device)

    def run(self):
        print "Device: '{}'".format(self._device)
        print "Discovering...",
        sys.stdout.flush()

        neighbors = self.local.discover()
        print "Done"
        self.printResults(neighbors)

    def printResults(self, neighbors):
        if not neighbors:
            print "No neighbors found!"
            return

        print "Results:"
        for i, n in enumerate(neighbors):
            print "{}: {}".format(i, n)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description = "Discover other nodes")

    parser.add_argument('-d', dest='device', default="/dev/ttyUSB0",
                        help="device where my XBee is attached")

    args = parser.parse_args()
    s = Discoverer(args.device)
    s.run()

