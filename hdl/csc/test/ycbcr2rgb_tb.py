from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from hdl.csc.common import *
from hdl.csc.ycbcr2rgb import ycbcr2rgb_coefs, YCbCr2RGB

from hdl.csc.test.common import *

class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)], packetized=True))
        self.submodules.ycbcr2rgb = YCbCr2RGB()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)], packetized=True))

        self.comb += [
            self.ycbcr2rgb.sink.stb.eq(self.streamer.source.stb),
            self.ycbcr2rgb.sink.sop.eq(self.streamer.source.sop),
            self.ycbcr2rgb.sink.eop.eq(self.streamer.source.eop),
            self.ycbcr2rgb.sink.payload.y.eq(self.streamer.source.data[16:24]),
            self.ycbcr2rgb.sink.payload.cb.eq(self.streamer.source.data[8:16]),
            self.ycbcr2rgb.sink.payload.cr.eq(self.streamer.source.data[0:8]),
            self.streamer.source.ack.eq(self.ycbcr2rgb.sink.ack),

            self.logger.sink.stb.eq(self.ycbcr2rgb.source.stb),
            self.logger.sink.sop.eq(self.ycbcr2rgb.source.sop),
            self.logger.sink.eop.eq(self.ycbcr2rgb.source.eop),
            self.logger.sink.data[16:24].eq(self.ycbcr2rgb.source.r),
            self.logger.sink.data[8:16].eq(self.ycbcr2rgb.source.g),
            self.logger.sink.data[0:8].eq(self.ycbcr2rgb.source.b),
            self.ycbcr2rgb.source.ack.eq(self.logger.sink.ack)
        ]

    def gen_simulation(self, selfp):
        # convert image using ycbcr2rgb model
        raw_image = RAWImage(ycbcr2rgb_coefs(8), "lena.png", 64)
        raw_image.rgb2ycbcr()
        raw_image.ycbcr2rgb_model()
        raw_image.save("lena_reference.png")

        for i in range(16):
            yield

        # convert image using ycbcr2rgb implementation
        raw_image = RAWImage(ycbcr2rgb_coefs(8), "lena.png", 64)
        raw_image.rgb2ycbcr()
        raw_image.pack_ycbcr()
        packet = Packet(raw_image.data)
        self.streamer.send(packet)
        yield from self.logger.receive()
        raw_image.set_data(self.logger.packet)
        raw_image.unpack_rgb()
        raw_image.save("lena_implementation.png")


if __name__ == "__main__":
    run_simulation(TB(), ncycles=8192, vcd_name="my.vcd", keep_files=True)
