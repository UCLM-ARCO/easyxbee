#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
from EasyXBee import LocalNode

if len(sys.argv) != 3:
    print "Usage: {} node message".format(sys.argv[0])
    sys.exit(1)

local = LocalNode(tty='/dev/ttyUSB1')
local.set_pan_id(0x2012)
remote = local.lookup(sys.argv[1])

remote.send(sys.argv[2])

