from litex.gen import *
from litex.soc.interconnect.stream import *
from litex.soc.interconnect.stream_sim import *

from gateware.csc.common import *
from gateware.csc.ycbcr444to422 import YCbCr444to422
from gateware.csc.ycbcr422to444 import YCbCr422to444

from gateware.csc.test.common import *


class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)]))
        self.submodules.ycbcr444to422 = YCbCr444to422()
        self.submodules.ycbcr422to444 = YCbCr422to444()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)]))

        self.comb += [
            Record.connect(self.streamer.source, self.ycbcr444to422.sink, leave_out=["data"]),
            self.ycbcr444to422.sink.payload.y.eq(self.streamer.source.data[16:24]),
            self.ycbcr444to422.sink.payload.cb.eq(self.streamer.source.data[8:16]),
            self.ycbcr444to422.sink.payload.cr.eq(self.streamer.source.data[0:8]),

            Record.connect(self.ycbcr444to422.source, self.ycbcr422to444.sink),

            Record.connect(self.ycbcr422to444.source, self.logger.sink, leave_out=["y", "cb", "cr"]),
            self.logger.sink.data[16:24].eq(self.ycbcr422to444.source.y),
            self.logger.sink.data[8:16].eq(self.ycbcr422to444.source.cb),
            self.logger.sink.data[0:8].eq(self.ycbcr422to444.source.cr)
        ]


def main_generator(dut):
    for i in range(16):
        yield

    # chain ycbcr444to422 and ycbcr422to444
    raw_image = RAWImage(None, "lena.png", 64)
    raw_image.rgb2ycbcr()
    raw_image.pack_ycbcr()
    packet = Packet(raw_image.data)
    dut.streamer.send(packet)
    yield from dut.logger.receive()
    raw_image.set_data(dut.logger.packet)
    raw_image.unpack_ycbcr()
    raw_image.ycbcr2rgb()
    raw_image.save("lena_resampling.png")

if __name__ == "__main__":
    tb = TB()
    generators = {"sys" : [main_generator(tb)]}
    generators = {
        "sys" :   [main_generator(tb),
                   tb.streamer.generator(),
                   tb.logger.generator()]
    }
    clocks = {"sys": 10}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
