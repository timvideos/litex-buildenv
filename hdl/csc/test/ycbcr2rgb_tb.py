from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from hdl.csc.common import *
from hdl.csc.ycbcr2rgb import ycbcr2rgb_coefs

from hdl.csc.test.common import *

class TB(Module):
    def __init__(self):
        self.submodules.streamer = PacketStreamer(EndpointDescription([("data", 24)], packetized=True))
        self.submodules.logger = PacketLogger(EndpointDescription([("data", 24)], packetized=True))


    def gen_simulation(self, selfp):
        # convert image using ycbcr2rgb model
        raw_image = RAWImage(ycbcr2rgb_coefs(8), "lena.png", 512)
        raw_image.rgb2ycbcr()
        raw_image.ycbcr2rgb_model()
        raw_image.save("lena_reference.png")

        yield

if __name__ == "__main__":
    run_simulation(TB(), ncycles=8192, vcd_name="my.vcd", keep_files=True)
