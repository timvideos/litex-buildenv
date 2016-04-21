#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.s7 import S7HDMIOutClocking
from litevideo.output.hdmi.s7 import S7HDMIOutPHY
from litevideo.output.core import TimingGenerator


class VideoOutSoC(BaseSoC):
    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")

        # # #

        self.submodules.timing = ClockDomainsRenamer("pix")(TimingGenerator())
        self.comb += [
            self.timing.sink.valid.eq(1),

            self.timing.sink.hres.eq(1280),
            self.timing.sink.hsync_start.eq(1390),
            self.timing.sink.hsync_end.eq(1430),
            self.timing.sink.hscan.eq(1650),

            self.timing.sink.vres.eq(720),
            self.timing.sink.vsync_start.eq(725),
            self.timing.sink.vsync_end.eq(730),
            self.timing.sink.vscan.eq(750)
        ]

        self.submodules.clocking = S7HDMIOutClocking(self.crg.clk100, pads)
        self.submodules.phy = S7HDMIOutPHY(pads)
        self.comb += [
            self.timing.source.connect(self.phy.sink),
            self.phy.sink.r.eq(0x00),
            self.phy.sink.g.eq(0x00),
            self.phy.sink.b.eq(0xff)
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

