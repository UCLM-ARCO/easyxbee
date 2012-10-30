#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
from EasyXBee import LocalNode

local = LocalNode(tty='/dev/ttyUSB1')
local.set_pan_id(0x2012)
remote = local.lookup("receiver")

remote.send(sys.argv[1])

