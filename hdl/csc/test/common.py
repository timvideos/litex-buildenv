from PIL import Image

import random
import copy

from migen.fhdl.std import *
from migen.flow.actor import Sink, Source
from migen.genlib.record import *


def seed_to_data(seed, random=True):
    if random:
        return (seed * 0x31415979 + 1) & 0xffffffff
    else:
        return seed


def comp(p1, p2):
    r = True
    for x, y in zip(p1, p2):
        if x != y:
            r = False
    return r


def check(p1, p2):
    p1 = copy.deepcopy(p1)
    p2 = copy.deepcopy(p2)
    if isinstance(p1, int):
        return 0, 1, int(p1 != p2)
    else:
        if len(p1) >= len(p2):
            ref, res = p1, p2
        else:
            ref, res = p2, p1
        shift = 0
        while((ref[0] != res[0]) and (len(res) > 1)):
            res.pop(0)
            shift += 1
        length = min(len(ref), len(res))
        errors = 0
        for i in range(length):
            if ref.pop(0) != res.pop(0):
                errors += 1
        return shift, length, errors


def randn(max_n):
    return random.randint(0, max_n-1)


class Packet(list):
    def __init__(self, init=[]):
        self.ongoing = False
        self.done = False
        for data in init:
            self.append(data)


class PacketStreamer(Module):
    def __init__(self, description, last_be=None):
        self.source = Source(description)
        self.last_be = last_be

        # # #

        self.packets = []
        self.packet = Packet()
        self.packet.done = True

    def send(self, packet):
        packet = copy.deepcopy(packet)
        self.packets.append(packet)
        return packet

    def send_blocking(self, packet):
        packet = self.send(packet)
        while not packet.done:
            yield

    def do_simulation(self, selfp):
        if len(self.packets) and self.packet.done:
            self.packet = self.packets.pop(0)
        if not self.packet.ongoing and not self.packet.done:
            selfp.source.stb = 1
            if self.source.description.packetized:
                selfp.source.sop = 1
            selfp.source.data = self.packet.pop(0)
            self.packet.ongoing = True
        elif selfp.source.stb == 1 and selfp.source.ack == 1:
            if self.source.description.packetized:
                selfp.source.sop = 0
                if len(self.packet) == 1:
                    selfp.source.eop = 1
                    if self.last_be is not None:
                        selfp.source.last_be = self.last_be
                else:
                    selfp.source.eop = 0
                    if self.last_be is not None:
                        selfp.source.last_be = 0
            if len(self.packet) > 0:
                selfp.source.stb = 1
                selfp.source.data = self.packet.pop(0)
            else:
                self.packet.done = True
                selfp.source.stb = 0


class PacketLogger(Module):
    def __init__(self, description):
        self.sink = Sink(description)

        # # #

        self.packet = Packet()

    def receive(self):
        self.packet.done = False
        while not self.packet.done:
            yield

    def do_simulation(self, selfp):
        selfp.sink.ack = 1
        if selfp.sink.stb:
            if self.sink.description.packetized:
                if selfp.sink.sop:
                    self.packet = Packet()
                    self.packet.append(selfp.sink.data)
                else:
                    self.packet.append(selfp.sink.data)
                if selfp.sink.eop:
                    self.packet.done = True
            else:
                self.packet.append(selfp.sink.data)


class AckRandomizer(Module):
    def __init__(self, description, level=0):
        self.level = level

        self.sink = Sink(description)
        self.source = Source(description)

        self.run = Signal()

        self.comb += \
            If(self.run,
                Record.connect(self.sink, self.source)
            ).Else(
                self.source.stb.eq(0),
                self.sink.ack.eq(0),
            )

    def do_simulation(self, selfp):
        n = randn(100)
        if n < self.level:
            selfp.run = 0
        else:
            selfp.run = 1


class RAWImage:
    def __init__(self, coefs, filename=None, size=None):
        self.r = None
        self.g = None
        self.b = None

        self.y = None
        self.cb = None
        self.cr = None

        self.data = []

        self.coefs = coefs
        self.size = size
        self.length = None

        if filename is not None:
            self.open(filename)


    def open(self, filename):
        img = Image.open(filename)
        if self.size is not None:
            img = img.resize((self.size, self.size), Image.ANTIALIAS)
        r, g, b = zip(*list(img.getdata()))
        self.set_rgb(r, g, b)


    def save(self, filename):
        img = Image.new("RGB" ,(self.size, self.size))
        img.putdata(list(zip(self.r, self.g, self.b)))
        img.save(filename)


    def set_rgb(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.length = len(r)


    def set_ycbcr(self, y, cb, cr):
        self.y = y
        self.cb = cb
        self.cr = cr
        self.length = len(y)


    def set_data(self, data):
        self.data = data


    def pack_rgb(self):
        self.data = []
        for i in range(self.length):
            data = (self.r[i] & 0xff) << 16
            data |= (self.g[i] & 0xff) << 8
            data |= (self.b[i] & 0xff) << 0
            self.data.append(data)
        return self.data


    def pack_ycbcr(self):
        self.data = []
        for i in range(self.length):
            data = (self.y[i] & 0xff) << 16
            data |= (self.cb[i] & 0xff) << 8
            data |= (self.cr[i] & 0xff) << 0
            self.data.append(data)
        return self.data


    def unpack_rgb(self):
        self.r = []
        self.g = []
        self.b = []
        for data in self.data:
            self.r.append((data >> 16) & 0xff)
            self.g.append((data >> 8) & 0xff)
            self.b.append((data >> 0) & 0xff)
        return self.r, self.g, self.b


    def unpack_ycbcr(self):
        self.y = []
        self.cb = []
        self.cr = []
        for data in self.data:
            self.y.append((data >> 16) & 0xff)
            self.cb.append((data >> 8) & 0xff)
            self.cr.append((data >> 0) & 0xff)
        return self.y, self.cb, self.cr


    # Model for our implementation
    def rgb2ycbcr_model(self):
        self.y  = []
        self.cb = []
        self.cr = []
        for r, g, b in zip(self.r, self.g, self.b):
            yraw = self.coefs["ca"]*(r-g) + self.coefs["cb"]*(b-g) + g
            self.y.append(int(yraw + self.coefs["yoffset"]))
            self.cb.append(int(self.coefs["cc"]*(b-yraw) + self.coefs["coffset"]))
            self.cr.append(int(self.coefs["cd"]*(r-yraw) + self.coefs["coffset"]))
        return self.y, self.cb, self.cr


    # Wikipedia implementation used as reference
    def rgb2ycbcr(self):
        self.y = []
        self.cb = []
        self.cr = []
        for r, g, b in zip(self.r, self.g, self.b):
            self.y.append(int(0.299*r + 0.587*g + 0.114*b))
            self.cb.append(int(-0.1687*r - 0.3313*g + 0.5*b + 128))
            self.cr.append(int(0.5*r - 0.4187*g - 0.0813*b + 128))
        return self.y, self.cb, self.cr


    # Model for our implementation
    def ycbcr2rgb_model(self):
        self.r = []
        self.g = []
        self.b = []
        for y, cb, cr in zip(self.y, self.cb, self.cr):
            self.r.append(int(y - self.coefs["yoffset"] + (cr - self.coefs["coffset"])*self.coefs["acoef"]))
            self.g.append(int(y - self.coefs["yoffset"] + (cb - self.coefs["coffset"])*self.coefs["bcoef"] + (cr - self.coefs["coffset"])*self.coefs["ccoef"]))
            self.b.append(int(y - self.coefs["yoffset"] + (cb - self.coefs["coffset"])*self.coefs["dcoef"]))
        return self.r, self.g, self.b


    # Wikipedia implementation used as reference
    def ycbcr2rgb(self):
        self.r = []
        self.g = []
        self.b = []
        for y, cb, cr in zip(self.y, self.cb, self.cr):
            self.r.append(int(y + (cr - 128) *  1.402))
            self.g.append(int(y + (cb - 128) * -0.34414 + (cr - 128) * -0.71414))
            self.b.append(int(y + (cb - 128) *  1.772))
        return self.r, self.g, self.b


