from litex.gen import *
from litex.soc.interconnect.stream import *
from litex.soc.interconnect.stream_sim import *

from gateware.csc.common import *
from gateware.csc.rgb2ycbcr import rgb2ycbcr_coefs, RGB2YCbCr

from gateware.csc.test.common import *


class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)]))
        self.submodules.rgb2ycbcr = RGB2YCbCr()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)]))

        self.comb += [
        	Record.connect(self.streamer.source, self.rgb2ycbcr.sink, leave_out=["data"]),
            self.rgb2ycbcr.sink.payload.r.eq(self.streamer.source.data[16:24]),
            self.rgb2ycbcr.sink.payload.g.eq(self.streamer.source.data[8:16]),
            self.rgb2ycbcr.sink.payload.b.eq(self.streamer.source.data[0:8]),

            Record.connect(self.rgb2ycbcr.source, self.logger.sink, leave_out=["y", "cb", "cr"]),
            self.logger.sink.data[16:24].eq(self.rgb2ycbcr.source.y),
            self.logger.sink.data[8:16].eq(self.rgb2ycbcr.source.cb),
            self.logger.sink.data[0:8].eq(self.rgb2ycbcr.source.cr)
        ]


def main_generator(dut):
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
    dut.streamer.send(packet)
    yield from dut.logger.receive()
    raw_image.set_data(dut.logger.packet)
    raw_image.unpack_ycbcr()
    raw_image.ycbcr2rgb()
    raw_image.save("lena_rgb2ycbcr.png")

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
