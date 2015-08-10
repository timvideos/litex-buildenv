from PIL import Image

from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from hdl.csc.common import *
from hdl.csc.rgb2ycbcr import RGB2YCbCr

from hdl.csc.test.common import *

coefs = hd_pal_coefs(8)


class RAWImage:
    def __init__(self, filename=None, size=None):
        self.r = None
        self.g = None
        self.b = None

        self.y = None
        self.cb = None
        self.cr = None

        self.data = []

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
            yraw = coefs["ca"]*(r-g) + coefs["cb"]*(b-g) + g
            self.y.append(yraw + coefs["yoffset"])
            self.cb.append(coefs["cc"]*(b-yraw) + coefs["coffset"])
            self.cr.append(coefs["cd"]*(r-yraw) + coefs["coffset"])
        return self.y, self.cb, self.cr


    # Wikipedia implementation used as reference
    def ycbcr2rgb(self):
        self.r = []
        self.g = []
        self.b = []
        for y, cb, cr in zip(self.y, self.cb, self.cr):
            self.r.append(int(y + (cr - 128) *  1.40200))
            self.g.append(int(y + (cb - 128) * -0.34414 + (cr - 128) * -0.71414))
            self.b.append(int(y + (cb - 128) *  1.77200))
        return self.r, self.g, self.b


class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)], packetized=True))
        self.submodules.rgb2ycbcr = RGB2YCbCr()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)], packetized=True))

        self.comb += [
            self.rgb2ycbcr.sink.stb.eq(self.streamer.source.stb),
            self.rgb2ycbcr.sink.sop.eq(self.streamer.source.sop),
            self.rgb2ycbcr.sink.eop.eq(self.streamer.source.eop),
            self.rgb2ycbcr.sink.payload.r.eq(self.streamer.source.data[16:24]),
            self.rgb2ycbcr.sink.payload.g.eq(self.streamer.source.data[8:16]),
            self.rgb2ycbcr.sink.payload.b.eq(self.streamer.source.data[0:8]),
            self.streamer.source.ack.eq(self.rgb2ycbcr.sink.ack),

            self.logger.sink.stb.eq(self.rgb2ycbcr.source.stb),
            self.logger.sink.sop.eq(self.rgb2ycbcr.source.sop),
            self.logger.sink.eop.eq(self.rgb2ycbcr.source.eop),
            self.logger.sink.data[16:24].eq(self.rgb2ycbcr.source.y),
            self.logger.sink.data[8:16].eq(self.rgb2ycbcr.source.cb),
            self.logger.sink.data[0:8].eq(self.rgb2ycbcr.source.cr),
            self.rgb2ycbcr.source.ack.eq(self.logger.sink.ack)
        ]


    def gen_simulation(self, selfp):
        # convert image using rgb2ycbcr model
        raw_image = RAWImage("lena.png", 64)
        raw_image.rgb2ycbcr_model()
        raw_image.ycbcr2rgb()
        raw_image.save("lena_reference.png")

        for i in range(16):
            yield

        # convert image using rgb2ycbcr implementation
        raw_image = RAWImage("lena.png", 64)
        raw_image.pack_rgb()
        packet = Packet(raw_image.data)
        self.streamer.send(packet)
        yield from self.logger.receive()
        raw_image.set_data(self.logger.packet)
        raw_image.unpack_ycbcr()
        raw_image.ycbcr2rgb()
        raw_image.save("lena_implementation.png")

if __name__ == "__main__":
    run_simulation(TB(), ncycles=8192, vcd_name="my.vcd", keep_files=True)
