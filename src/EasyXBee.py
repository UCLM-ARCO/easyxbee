# -*- mode: python; coding: utf-8 -*-

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
        if response['status'] != '\x00':
            raise CommandError(response);
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

    def write_config(self):
        self.send_command("WR")

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
        return "<RemoteNode: name: '{}', 16-bit addr: '0x{:04x}', {}".format(
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
    def __init__(self, device=None, tty='/dev/ttyUSB0', speed=9600):
        if device is None:
            device = XBeeDevice(tty, speed)
        else:
            assert isinstance(device, XBeeDevice)

        self.device = device

    def set_pan_id(self, value):
        assert type(value) is int
        if self.get_pan_id() == value:
            return

        value = struct.pack('>Q', value)
        self.device.send_command("ID", value)

        # this command sends two frames, discards the second
        self.device.receive_frame()

    def get_pan_id(self):
        response = self.device.send_command("ID")
        return struct.unpack('>Q', response['parameter'])[0]

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

    def lookup(self, name):
        self.device.send_command("DN", str(name), wait_response=False)

        timeout = float(self.get_node_discovery_timeout())
        timeout = timeout / 1000 + 0.25
        rlist = select([self.device.serial], [], [], timeout)[0]

        if not rlist:
            raise HardwareError("Module XBee not responding")

        response = self.device.receive_frame()
        if response['status'] != '\x00':
            raise CommandError(response)

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
            if response['status'] != '\x00':
                raise CommandError(response)
            nodes.append(RemoteNode.create_from_nd_response(self.device, response))

        return nodes

    def get_node_discovery_timeout(self):
        response = self.device.send_command("NT")

        # NT is multiplied by 100 to get the real time, in ms
        return struct.unpack(">H", response['parameter'])[0] * 100

    def receive(self):
        message = self.device.receive_frame()
        return message['rf_data']


