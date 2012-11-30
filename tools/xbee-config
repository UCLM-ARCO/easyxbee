#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import argparse
import time

from EasyXBee import LocalNode


class SetupTool:
    def __init__(self, args):
        self.local = LocalNode(tty=args.device)
        self.args = args

    def run(self):
        if self.show_info():
            return
        if self.check_config():
            return
        if self.reset_device():
            return

        self.config_panid()
        self.config_name()
        self.write_configuration()

    def show_info(self):
        if not self.args.info:
            return False

        api_level = self.local.get_api_level()
        sleep_mode = self.local.get_sleep_mode()
        panid = self.local.get_pan_id(False)
        name = self.local.get_name()
        role = self.local.get_role()[1]

        if sleep_mode == -1:
            sleep_mode = "<not available>"

        print ("Current info:\n"
               " - Role: {}\n".format(role) +
               " - PAN id: '{}'\n".format(panid) +
               " - Name: '{}'\n".format(name) +
               " - API level: {}\n".format(api_level) +
               " - Sleep mode: {}\n".format(sleep_mode))

        return True

    def check_config(self):
        if not self.args.check:
            return False

        api_level = self.local.get_api_level()
        sleep_mode = self.local.get_sleep_mode()
        print "Device: {}, API Level: {}, sleep mode: {}".format(
            self.args.device, api_level, sleep_mode)

        if api_level == 1 and sleep_mode <= 0:
            print "It seems correct!"
        else:
            if api_level != 1:
                print "- API Level not compatible with this library"
            if sleep_mode > 0:
                print ("- Sleep mode enabled, this will cause many delays "
                       "when communicating with device")

        return True

    def reset_device(self):
        if not self.args.reset:
            return False

        print "Resetting device...",
        sys.stdout.flush()

        self.local.reset_device()
        time.sleep(2)

        print "Done"
        return True

    def config_panid(self):
        if not self.args.panid:
            return

        print "Setting PAN identifier to '{}'".format(self.args.panid)
        self.local.set_pan_id(self.args.panid)

    def config_name(self):
        if not self.args.nodename:
            return

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

    parser.add_argument('-r', dest='reset', action='store_true',
                        help="Make a software reset on device")
    parser.add_argument('-i', dest='info', action='store_true',
                        help="Show current configuration")
    parser.add_argument('-s', dest='save', action='store_true',
                        help="Save changes permanently")
    parser.add_argument('-c', dest='check', action='store_true',
                        help="Check for correct settings")

    args = parser.parse_args()
    s = SetupTool(args)
    s.run()
