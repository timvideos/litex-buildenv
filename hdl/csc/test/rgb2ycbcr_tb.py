from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from hdl.csc.common import *
from hdl.csc.rgb2ycbcr import rgb2ycbcr_coefs, RGB2YCbCr

from hdl.csc.test.common import *


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
        raw_image = RAWImage(rgb2ycbcr_coefs(8), "lena.png", 64)
        raw_image.rgb2ycbcr_model()
        raw_image.ycbcr2rgb()
        raw_image.save("lena_rgb2ycbcr_reference.png")

        for i in range(16):
            yield

        # convert image using rgb2ycbcr implementation
        raw_image = RAWImage(rgb2ycbcr_coefs(8), "lena.png", 64)
        raw_image.pack_rgb()
        packet = Packet(raw_image.data)
        self.streamer.send(packet)
        yield from self.logger.receive()
        raw_image.set_data(self.logger.packet)
        raw_image.unpack_ycbcr()
        raw_image.ycbcr2rgb()
        raw_image.save("lena_rgb2ycbcr.png")

if __name__ == "__main__":
    run_simulation(TB(), ncycles=8192, vcd_name="my.vcd", keep_files=True)
