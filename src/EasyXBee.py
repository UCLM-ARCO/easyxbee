# -*- mode: python; coding: utf-8 -*-

#
# Copyright (c) 2012 Oscar Aceña. All rights reserved.
#
# This file is part of EasyXBee.
#
# EasyXBee is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EasyXBee is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyXBee.  If not, see <http://www.gnu.org/licenses/>.
#

from xbee import ZigBee
import serial
import struct
import time
from select import select


class CommandError(Exception):
    def __init__(self, response):
        Exception.__init__(self, str(response))


class HardwareError(Exception):
    pass


class XBeeDevice(object):
    def __init__(self, tty='/dev/ttyUSB0', speed=9600):
        self.serial = serial.Serial(tty, speed)
        self.xbee = ZigBee(self.serial)

    def __del__(self):
        self.serial.close()

    def send_command(self, cmd, param=None, wait_response=True):
        self.xbee.at(command=cmd, parameter=param)

        if not wait_response:
            return

        response = self.xbee.wait_read_frame()
        if response.get('status') != '\x00':
            raise CommandError(response)
        return response

    def send_data(self, addr, addr_long, data):
        addr = struct.pack('>H', addr)
        addr_long = struct.pack('>Q', addr_long)

        self.xbee.send('tx', dest_addr_long=addr_long, dest_addr=addr, data=data)
        response = self.xbee.wait_read_frame()
        if response['deliver_status'] != '\x00':
            raise CommandError(response)

    def receive_frame(self):
        return self.xbee.wait_read_frame()

    def data_available(self, timeout=0):
        for i in range(int(timeout * 10)):
            time.sleep(0.1)
            if self.serial.inWaiting() > 0:
                return True
        return self.serial.inWaiting() > 0

    def get_max_payload_size(self):
        response = self.send_command("NP")
        return struct.unpack(">H", response['parameter'])[0]


class RemoteNode(object):
    def __init__(self, device):
        self.device = device
        self.xbee = None
        self.name = ""
        self.my_addr = None
        self.hw_addr = None
        self.role = 255

    def __unicode__(self):
        return "<RemoteNode: name: '{}', 16-bit addr: '0x{:04x}', {}>".format(
            self.name, self.my_addr, self.get_role_name())

    def __repr__(self):
        return unicode(self)

    def get_role_name(self):
        try:
            return ["coordinator",
                    "router",
                    "end device",
                    ][self.role]
        except IndexError:
            return "unknown role (0x{:x})".format(self.role)

    def send(self, data):
        self.device.send_data(self.my_addr, self.hw_addr, data)

    @classmethod
    def create_from_nd_response(cls, device, response):
        node = RemoteNode(device)
        data = response['parameter']
        i = 0

        # MY (2 Bytes)
        node.my_addr = struct.unpack(">H", data[i:i + 2])[0]
        i += 2

        # SH (4 Bytes) + SL (4 Bytes)
        node.hw_addr = struct.unpack(">Q", data[i:i + 8])[0]
        i += 8

        # NI (Variable length) + \0
        while True:
            c = data[i]
            i += 1
            if c == "\x00":
                break
            node.name += c

        # PARENT_NETWORK ADDRESS (2 Bytes)
        i += 2

        # DEVICE_TYPE (1 Byte)
        node.role = ord(data[i])
        i += 1

        # STATUS (1 Byte)
        # PROFILE_ID (2 Bytes)
        # MANUFACTURER_ID (2 Bytes)

        return node

    @classmethod
    def create_from_dn_response(cls, device, response):
        node = RemoteNode(device)
        data = response['parameter']

        # MY (2 Bytes)
        node.my_addr = struct.unpack(">H", data[:2])[0]

        # SH (4 Bytes) + SL (4 Bytes)
        node.hw_addr = struct.unpack(">Q", data[2:10])[0]

        return node


class LocalNode(object):
    def __init__(self, device=None, tty='/dev/ttyUSB0', speed=57600):
        if device is None:
            device = XBeeDevice(tty, speed)
        else:
            assert isinstance(device, XBeeDevice)

        self.device = device

    def get_id_as_int64(self, value):
        for i in range(8 - len(value)):
            value += '\x00'
        return struct.unpack(">Q", value)[0]

    def set_pan_id(self, value):
        if not type(value) is int:
            value = self.get_id_as_int64(value)

        if self.get_pan_id() == value:
            return

        value = struct.pack('>Q', value)
        self.device.send_command("ID", value)

        # this command sends two frames, discards the second
        if self.device.data_available(0.5):
            self.device.receive_frame()

    def get_pan_id(self, unpack=True):
        response = self.device.send_command("ID")
        if not unpack:
            return response['parameter']
        return struct.unpack('>Q', response['parameter'])[0]

    def get_api_level(self):
        response = self.device.send_command("AP")
        return ord(response['parameter'])

    def get_role(self):
        response = self.device.send_command("VR")
        fver = hex(struct.unpack('>H', response['parameter'])[0])
        return {'1': (0, 'coordinator'),
                '3': (1, 'router'),
                '9': (2, 'end device')}[fver[3]]

    def get_sleep_mode(self):
        # Coordinator doesn't have sleep modes
        if self.get_role()[0] == 0:
            return -1

        response = self.device.send_command("SM")
        return ord(response['parameter'])

    def get_my_address(self):
        response = self.device.send_command("MY")
        return struct.unpack('>H', response['parameter'])[0]

    def get_name(self):
        response = self.device.send_command("NI")
        return response['parameter']

    def set_name(self, name):
        if self.get_name() == name:
            return

        self.device.send_command("NI", str(name))

    def write_config(self):
        self.device.send_command("WR")

    def reset_device(self):
        self.device.send_command("FR")

    def is_alive(self):
        self.device.send_command("VR")
        return True

    def lookup(self, name):
        self.device.send_command("DN", str(name), wait_response=False)

        timeout = float(self.get_node_discovery_timeout())
        timeout = timeout / 1000 + 0.25
        rlist = select([self.device.serial], [], [], timeout)[0]

        if not rlist:
            raise HardwareError("Module XBee not responding")

        response = self.device.receive_frame()
        if response.get('status') != '\x00':
            # node not found
            return None

        node = RemoteNode.create_from_dn_response(self.device, response)
        node.name = name
        return node

    def discover(self):
        timeout = float(self.get_node_discovery_timeout())
        timeout = timeout / 1000 + 0.25

        self.device.send_command("ND", wait_response=False)

        # if timeout is waited in select, it may be waited more than
        # once (at least, a bit of it in first place, and the whole
        # after the last response arrived)
        time.sleep(timeout)

        nodes = []
        while True:
            rlist = select([self.device.serial], [], [], 0.1)[0]
            if not rlist:
                break

            response = self.device.receive_frame()
            if response.get('status') != '\x00':
                raise CommandError(response)
            nodes.append(RemoteNode.create_from_nd_response(self.device, response))

        return nodes

    def get_node_discovery_timeout(self):
        response = self.device.send_command("NT")

        # NT is multiplied by 100 to get the real time, in ms
        return struct.unpack(">H", response['parameter'])[0] * 100

    def receive(self):
        while True:
            message = self.device.receive_frame()
            if 'rf_data' in message:
                return message['rf_data']
