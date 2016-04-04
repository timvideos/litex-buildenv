from litex.gen import *
from litex.soc.interconnect.stream import *
from litex.soc.interconnect.stream_sim import *

from gateware.csc.common import *
from gateware.csc.ycbcr2rgb import ycbcr2rgb_coefs, YCbCr2RGB

from gateware.csc.test.common import *

class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)]))
        self.submodules.ycbcr2rgb = YCbCr2RGB()
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)]))

        self.comb += [
            Record.connect(self.streamer.source, self.ycbcr2rgb.sink, leave_out=["data"]),
            self.ycbcr2rgb.sink.payload.y.eq(self.streamer.source.data[16:24]),
            self.ycbcr2rgb.sink.payload.cb.eq(self.streamer.source.data[8:16]),
            self.ycbcr2rgb.sink.payload.cr.eq(self.streamer.source.data[0:8]),

            Record.connect(self.ycbcr2rgb.source, self.logger.sink, leave_out=["r", "g", "b"]),
            self.logger.sink.data[16:24].eq(self.ycbcr2rgb.source.r),
            self.logger.sink.data[8:16].eq(self.ycbcr2rgb.source.g),
            self.logger.sink.data[0:8].eq(self.ycbcr2rgb.source.b)
        ]

def main_generator(dut):
    # convert image using ycbcr2rgb model
    raw_image = RAWImage(ycbcr2rgb_coefs(8), "lena.png", 64)
    raw_image.rgb2ycbcr()
    raw_image.ycbcr2rgb_model()
    raw_image.save("lena_ycbcr2rgb_reference.png")

    for i in range(16):
        yield

    # convert image using ycbcr2rgb implementation
    raw_image = RAWImage(ycbcr2rgb_coefs(8), "lena.png", 64)
    raw_image.rgb2ycbcr()
    raw_image.pack_ycbcr()
    packet = Packet(raw_image.data)
    dut.streamer.send(packet)
    yield from dut.logger.receive()
    raw_image.set_data(dut.logger.packet)
    raw_image.unpack_rgb()
    raw_image.save("lena_ycbcr2rgb.png")


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
