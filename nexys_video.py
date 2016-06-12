#!/usr/bin/env python3

from nexys_base import *

from litex.soc.interconnect import stream

from litevideo.output.common import *
from litevideo.output.hdmi.s7 import S7HDMIOutClocking
from litevideo.output.hdmi.s7 import S7HDMIOutPHY
from litevideo.output.core import Initiator, TimingGenerator
from litevideo.output.pattern import ColorBarsPattern

base_cls = MiniSoC


class VideoOutSoC(base_cls):
    csr_map = {
        "initiator": 21,
        "clocking":  22
    }
    csr_map.update(base_cls.csr_map)

    def __init__(self, platform, *args, **kwargs):
        base_cls.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")

        # # #

        self.submodules.initiator = Initiator("pix")
        self.submodules.timing = ClockDomainsRenamer("pix")(TimingGenerator())
        self.submodules.pattern = ClockDomainsRenamer("pix")(ColorBarsPattern())
        self.comb += [
            self.initiator.source.connect(self.timing.sink, omit=["base", "end"]),
            self.pattern.sink.valid.eq(self.timing.sink.valid),
            self.pattern.sink.hres.eq(self.timing.sink.hres)
        ]

        self.submodules.clocking = S7HDMIOutClocking(pads)
        self.submodules.phy = S7HDMIOutPHY(pads)

        self.comb += [
            self.phy.sink.valid.eq(self.timing.source.valid),
            self.phy.sink.de.eq(self.timing.source.de),
            self.phy.sink.hsync.eq(self.timing.source.hsync),
            self.phy.sink.vsync.eq(self.timing.source.vsync),
            self.phy.sink.r.eq(self.pattern.source.r),
            self.phy.sink.g.eq(self.pattern.source.g),
            self.phy.sink.b.eq(self.pattern.source.b),
            self.pattern.source.ready.eq(self.timing.source.de),
            self.timing.source.ready.eq(1),
        ]


def main():
    parser = argparse.ArgumentParser(description="Nexys LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = nexys.Platform()
    soc = VideoOutSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()

