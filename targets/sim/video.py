from migen import *

from litevideo.output.common import *
from litevideo.output.core import VideoOutCore

from targets.utils import csr_map_update
from targets.sim.net import NetSoC as BaseSoC


class VGAModel(Module):
    def __init__(self, pads):
        self.sink = sink = stream.Endpoint(video_out_layout(24))
        self.comb += [
            sink.ready.eq(1),
            pads.de.eq(sink.de),
            pads.hsync.eq(sink.hsync),
            pads.vsync.eq(sink.vsync),
            pads.r.eq(sink.data[0:8]),
            pads.g.eq(sink.data[8:16]),
            pads.b.eq(sink.data[16:24]),
        ]


class VideoSoC(BaseSoC):
    csr_peripherals = {
        "video_out": 20,
    }
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, *args, **kwargs):
        BaseSoC.__init__(self, *args, **kwargs)

        self.submodules.video_out = VideoOutCore(self.sdram.crossbar.get_port())
        self.submodules.vga = VGAModel(platform.request("vga"))
        self.comb += self.video_out.source.connect(self.vga.sink)
