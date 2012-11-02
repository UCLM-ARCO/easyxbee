#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

from EasyXBee import LocalNode

node = LocalNode(tty='/dev/ttyUSB1')
node.set_pan_id(0x2012)
node.set_name("receiver")
node.write_config()

while True:
    try:
        print list(node.receive())
    except KeyboardInterrupt:
        print "\rBye!"
        break
