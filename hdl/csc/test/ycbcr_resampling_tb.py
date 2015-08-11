from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from hdl.csc.common import *
from hdl.csc.ycbcr444to422 import YCbCr444to422
from hdl.csc.ycbcr422to444 import YCbCr422to444

from hdl.csc.test.common import *


class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)], packetized=True))
        self.submodules.ycbcr444to422 = YCbCr444to422()
        self.submodules.ycbcr422to444 = YCbCr422to444()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)], packetized=True))

        self.comb += [
            self.ycbcr444to422.sink.stb.eq(self.streamer.source.stb),
            self.ycbcr444to422.sink.sop.eq(self.streamer.source.sop),
            self.ycbcr444to422.sink.eop.eq(self.streamer.source.eop),
            self.ycbcr444to422.sink.payload.y.eq(self.streamer.source.data[16:24]),
            self.ycbcr444to422.sink.payload.cb.eq(self.streamer.source.data[8:16]),
            self.ycbcr444to422.sink.payload.cr.eq(self.streamer.source.data[0:8]),
            self.streamer.source.ack.eq(self.ycbcr444to422.sink.ack),

            Record.connect(self.ycbcr444to422.source, self.ycbcr422to444.sink),

            self.logger.sink.stb.eq(self.ycbcr422to444.source.stb),
            self.logger.sink.sop.eq(self.ycbcr422to444.source.sop),
            self.logger.sink.eop.eq(self.ycbcr422to444.source.eop),
            self.logger.sink.data[16:24].eq(self.ycbcr422to444.source.y),
            self.logger.sink.data[8:16].eq(self.ycbcr422to444.source.cb),
            self.logger.sink.data[0:8].eq(self.ycbcr422to444.source.cr),
            self.ycbcr422to444.source.ack.eq(self.logger.sink.ack)
        ]


    def gen_simulation(self, selfp):
        for i in range(16):
            yield

        # chain ycbcr444to422 and ycbcr422to444
        raw_image = RAWImage(None, "lena.png", 64)
        raw_image.rgb2ycbcr()
        raw_image.pack_ycbcr()
        packet = Packet(raw_image.data)
        self.streamer.send(packet)
        yield from self.logger.receive()
        raw_image.set_data(self.logger.packet)
        raw_image.unpack_ycbcr()
        raw_image.ycbcr2rgb()
        raw_image.save("lena_resampling.png")

if __name__ == "__main__":
    run_simulation(TB(), ncycles=8192, vcd_name="my.vcd", keep_files=True)
