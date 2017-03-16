# -*- mode: python; coding: utf-8 -*-

#
# Copyright (c) 2012-2017 Oscar Aceña. All rights reserved.
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
import sys
from select import select
from collections import deque


class CommandError(Exception):
    def __init__(self, response):
        self.response = response
        Exception.__init__(self, str(response))


class HardwareError(Exception):
    pass


def get_parameter(response):
    data = response.get(b'parameter')
    if data is None:
        raise CommandError(response)
    return data


class XBeeDevice(object):
    def __init__(self, tty='/dev/ttyUSB0', speed=9600):
        self.serial = serial.Serial(tty, speed)
        self.xbee = ZigBee(self.serial)
        self.msg_buffer = deque(maxlen=25)

    def __del__(self):
        if hasattr(self, "serial"):
            self.serial.close()

    def wait_read_frame(self, expected_id, expected_cmd=None):
        if expected_cmd is not None:
            expected_cmd = expected_cmd.lower()

        print("wait read frame")
        while True:
            while self.data_available():
                frame = self.xbee.wait_read_frame()
                self.msg_buffer.append(frame)

            for i in reversed(list(range(len(self.msg_buffer)))):
                frame = self.msg_buffer[i]
                frame_cmd = frame.get(b'command')
                if frame_cmd is not None:
                    frame_cmd = frame_cmd.lower()
                frame_id = frame.get(b'id')

                if (frame_id == expected_id):
                    if (expected_cmd is None or expected_cmd == frame_cmd):
                        self.msg_buffer.remove(frame)
                        return frame

    def send_command(self, cmd, param=None, wait_response=True):
        self.xbee.at(command=cmd, parameter=param)

        if not wait_response:
            return

        response = self.wait_read_frame(b'at_response', cmd)
        if response.get(b'status') != b'\x00':
            raise CommandError(response)
        return response

    def send_data(self, addr, addr_long, data):
        addr = struct.pack('>H', addr)
        addr_long = struct.pack('>Q', addr_long)

        self.xbee.send(b'tx', dest_addr_long=addr_long,
                       dest_addr=addr, data=data)

        response = self.wait_read_frame(b'tx_status')
        if response.get(b'deliver_status') != b'\x00':
            raise CommandError(response)

    def receive_frame(self):
        return self.wait_read_frame(b'rx')

    def data_available(self, timeout=0):
        for i in range(int(timeout * 10)):
            time.sleep(0.1)
            if self.serial.inWaiting() > 0:
                return True
        return self.serial.inWaiting() > 0

    def get_max_payload_size(self):
        response = self.send_command(b"NP")
        size = get_parameter(response)
        return struct.unpack(">H", size)[0]


class RemoteNode(object):
    def __init__(self, device):
        self.device = device
        self.xbee = None
        self.name = b""
        self.my_addr = None
        self.hw_addr = None
        self.role = 255

    def __unicode__(self):
        return "<RemoteNode: name: '{}', 16-bit addr: '0x{:04x}', {}>".format(
            self.name, self.my_addr, self.get_role_name())

    def __repr__(self):
        return str(self)

    def get_role_name(self):
        try:
            return [b"coordinator",
                    b"router",
                    b"end device",
                    ][self.role]
        except IndexError:
            return "unknown role (0x{:x})".format(self.role)

    def send(self, data):
        self.device.send_data(self.my_addr, self.hw_addr, data)

    @classmethod
    def create_from_nd_response(cls, device, response):
        node = RemoteNode(device)
        data = get_parameter(response)

        # MY (2 Bytes)
        node.my_addr = struct.unpack(">H", data[b'source_addr'])[0]

        # SH (4 Bytes) + SL (4 Bytes)
        node.hw_addr = struct.unpack(">Q", data[b'source_addr_long'])[0]

        # NI (Variable length) + \0
        node.name = data[b'node_identifier']

        # DEVICE_TYPE (1 Byte)
        node.role = ord(data[b'device_type'])

        return node

    @classmethod
    def create_from_dn_response(cls, device, response):
        node = RemoteNode(device)
        data = get_parameter(response)

        # MY (2 Bytes)
        node.my_addr = struct.unpack(">H", data[:2])[0]

        # SH (4 Bytes) + SL (4 Bytes)
        node.hw_addr = struct.unpack(">Q", data[2:10])[0]

        return node


class LocalNode(object):
    def __init__(self, device=None, tty='/dev/ttyUSB0', speed=9600):
        if device is None:
            device = XBeeDevice(tty, speed)
        else:
            assert isinstance(device, XBeeDevice)

        self.device = device

    def get_id_as_int64(self, value):
        value = bytes(value, "utf-8")
        for i in range(8 - len(value)):
            value += b'\x00'
        return struct.unpack(">Q", value)[0]

    def set_pan_id(self, value):
        if not type(value) is int:
            value = self.get_id_as_int64(value)

        if self.get_pan_id() == value:
            return

        value = struct.pack('>Q', value)
        self.device.send_command(b"ID", value)

        # # this command sends two frames, discards the second
        # if self.device.data_available(0.5):
        #     self.device.wait_read_frame(b'at_response')

    def get_pan_id(self, unpack=True):
        response = self.device.send_command(b"ID")
        pan = get_parameter(response)

        if not unpack:
            return pan
        return struct.unpack('>Q', pan)[0]

    def get_api_level(self):
        response = self.device.send_command(b"AP")
        level = get_parameter(response)
        return ord(level)

    def get_role(self):
        response = self.device.send_command(b"VR")
        role = get_parameter(response)

        fver = hex(struct.unpack('>H', role)[0])
        return {b'1': (0, b'coordinator'),
                b'3': (1, b'router'),
                b'9': (2, b'end device')}[fver[3]]

    def get_sleep_mode(self):
        # Coordinator doesn't have sleep modes
        if self.get_role()[0] == 0:
            return -1

        response = self.device.send_command(b"SM")
        mode = get_parameter(response)
        return ord(mode)

    def get_my_address(self):
        response = self.device.send_command(b"MY")
        addr = get_parameter(response)
        return struct.unpack('>H', addr)[0]

    def get_name(self):
        response = self.device.send_command(b"NI")
        return get_parameter(response)

    def set_name(self, name):
        if self.get_name() == name:
            return

        self.device.send_command(b"NI", str(name))

    def write_config(self):
        self.device.send_command(b"WR")

    def reset_device(self):
        self.device.send_command(b"FR")

    def is_alive(self):
        self.device.send_command(b"VR")
        return True

    def lookup(self, name):
        timeout = float(self.get_node_discovery_timeout())
        timeout = timeout / 1000 + 0.25

        self.device.send_command(b"DN", str(name), wait_response=False)
        rlist = select([self.device.serial], [], [], timeout)[0]

        if not rlist:
            raise HardwareError("Module XBee not responding")

        response = self.device.wait_read_frame(b'at_response')
        if response.get(b'status') != b'\x00':
            # node not found
            return None

        node = RemoteNode.create_from_dn_response(self.device, response)
        node.name = name
        return node

    def discover(self):
        timeout = float(self.get_node_discovery_timeout())
        timeout = timeout / 1000 + 0.25

        self.device.send_command(b"ND", wait_response=False)

        nodes = []
        while True:
            rlist = select([self.device.serial], [], [], timeout)[0]
            if not rlist:
                break

            response = self.device.wait_read_frame(b'at_response')

            if response.get(b'status') != b'\x00':
                raise CommandError(response)
            nodes.append(
                RemoteNode.create_from_nd_response(self.device, response))

            sys.stdout.write(".")
            sys.stdout.flush()

        return nodes

    def get_node_discovery_timeout(self):
        response = self.device.send_command(b"NT")

        # NT is multiplied by 100 to get the real time, in ms
        timeout = get_parameter(response)
        return struct.unpack(">H", timeout)[0] * 100

    def receive(self):
        while True:
            message = self.device.receive_frame()
            data = message.get(b'rf_data')
            if data:
                return data
