#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import argparse

from EasyXBee import LocalNode

def send(dst, message):
    local = LocalNode()
    local.set_pan_id("mypan")

    remote = local.lookup(dst)
    remote.send(message)

send("node2", "Hello node2!")
