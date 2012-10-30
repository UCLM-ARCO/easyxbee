#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

from EasyXBee import LocalNode

myself = LocalNode(tty='/dev/ttyUSB1')
neighbors = myself.discover()

for n in neighbors:
    print n
