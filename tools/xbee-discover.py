#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import argparse

from EasyXBee import LocalNode


class Discoverer:
    def __init__(self, device, panid):
        self._device = device
        self._panid = panid

        self.local = LocalNode(tty=device)
        self.local.set_pan_id(panid)

    def run(self):
        print "Device: '{}', PAN: '{}'".format(self._device, self._panid)
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
    parser.add_argument('-p', dest='panid', default="net",
                        help="PAN identifier on wich search node")

    args = parser.parse_args()
    s = Discoverer(args.device, args.panid)
    s.run()

