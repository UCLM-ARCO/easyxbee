#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

from EasyXBee import LocalNode

serial = '/dev/ttyUSB1'
pan_id = 'net'
name   = 'coordinator'

print ("SETUP node...\n - PAN id: {}\n - name: {}\n - port: {}\n"
       .format(pan_id, name, serial))

node = LocalNode(tty=serial)
node.set_pan_id(pan_id)
node.set_name(name)
node.write_config()


print "OK, listen events..."

while True:
    try:
        print list(node.receive())
    except KeyboardInterrupt:
        print "\rBye!"
        break
