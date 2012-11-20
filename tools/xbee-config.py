#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import argparse

from EasyXBee import LocalNode


class SetupTool:
    def __init__(self, args):
        self.local = LocalNode(tty=args.device)
        self.args = args

    def run(self):
        if not self.check_options():
            return

        if self.args.info:
            self.show_info()
            return

        self.config_panid()
        self.config_name()
        self.write_configuration()

    def show_info(self):
        panid = self.local.get_pan_id(False)
        name = self.local.get_name()

        print ("Current info:\n"
               " - PAN id: '{}'\n"
               " - name: '{}'".format(panid, name))

    def check_options(self):
        if (self.args.panid or
            self.args.nodename or
            self.args.info or
            self.args.save) :
            return True

        print "No options given, nothing to do."
        return False

    def config_panid(self):
        if self.args.panid:
            print "Setting PAN identifier to '{}'".format(self.args.panid)
            self.local.set_pan_id(self.args.panid)

    def config_name(self):
        if self.args.nodename:
            print "Setting node name to '{}'".format(self.args.nodename)
            self.local.set_name(self.args.nodename)

    def write_configuration(self):
        if self.args.save:
            print "Making configuration permanent"
            self.local.write_config()
        else:
            print "This configuration will not be permanent"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description = "Configure a XBee device")

    parser.add_argument('-d', dest='device', default="/dev/ttyUSB1",
                        help="Device where the XBee module is attached")

    parser.add_argument('-p', dest='panid',
                        help="PAN identifier")
    parser.add_argument('-n', dest='nodename',
                        help="Name for this device")

    parser.add_argument('-i', dest='info', action='store_true',
                        help="Show current configuration")
    parser.add_argument('-s', dest='save', action='store_true',
                        help="Save changes permanently")

    args = parser.parse_args()
    s = SetupTool(args)
    s.run()
