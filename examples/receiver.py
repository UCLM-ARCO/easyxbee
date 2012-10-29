#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

from EasyXBee import LocalNode

node = LocalNode(tty='/dev/ttyUSB0')
node.set_pan_id(2012)
node.set_name("receiver")

while True:
    try:
        print node.receive()
    except KeyboardInterrupt:
        print "\rBye!"
        break
