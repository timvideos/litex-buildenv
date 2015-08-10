from PIL import Image

from migen.fhdl.std import *
from migen.sim.generic import run_simulation

from hdl.csc.common import *
from hdl.csc.rgb2ycbcr import RGB2YCbCr

from hdl.csc.test.common import *

coefs = hd_pal_coefs(8)


# Model for our implementation
def rgb2ycbcr_model(r, g, b):
    y  = []
    cb = []
    cr = []
    for i in range(len(min(r, g, b))):
        yraw = coefs["ca"]*(r[i]-g[i]) + coefs["cb"]*(b[i]-g[i]) + g[i]
        y.append(yraw + coefs["yoffset"])
        cb.append(coefs["cc"]*(b[i]-yraw) + coefs["coffset"])
        cr.append(coefs["cd"]*(r[i]-yraw) + coefs["coffset"])
    return y, cb, cr


# Wikipedia implementation used as reference
def ycbcr2rgb(y, cb, cr):
    r = []
    g = []
    b = []
    for i in range(len(min(y, cb, cr))):
        r.append(int(y[i] + (cr[i] - 128) *  1.40200))
        g.append(int(y[i] + (cb[i] - 128) * -0.34414 + (cr[i] - 128) * -0.71414))
        b.append(int(y[i] + (cb[i] - 128) *  1.77200))
    return r, g, b


class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer([("data", 24)])
        self.submodules.rgb2ycbcr = RGB2YCbCr() # XXX use params
        self.submodules.logger = PacketLogger([("data", 24)])

        self.comb += [
            self.rgb2ycbcr.sink.stb.eq(self.streamer.source.stb),
            self.rgb2ycbcr.sink.payload.raw_bits().eq(self.streamer.source.raw_bits()),
            self.streamer.source.ack.eq(self.rgb2ycbcr.sink.ack),

            self.logger.sink.stb.eq(self.rgb2ycbcr.source.stb),
            self.logger.sink.payload.raw_bits().eq(self.rgb2ycbcr.source.raw_bits()),
            self.rgb2ycbcr.source.ack.eq(self.logger.sink.ack)
        ]

    def gen_simulation(self, selfp):
        for i in range(16):
            packet = Packet([randn(2**24) for i in range(128)])
            self.streamer.send(packet)
            yield from self.logger.receive()


if __name__ == "__main__":
    img_size = 128
    img = Image.open("lena.png")
    img = img.resize((img_size, img_size), Image.ANTIALIAS)
    r, g, b = zip(*list(img.getdata()))
    img_len = len(r)

    y, cb, cr = rgb2ycbcr_model(r, g, b)
    r, g, b = ycbcr2rgb(y, cb, cr)
    img = Image.new("RGB" ,(img_size, img_size))
    img.putdata(list(zip(r,g,b)))
    img.save("lena_tb_model.png")

    run_simulation(TB(), ncycles=4096, vcd_name="my.vcd", keep_files=True)

