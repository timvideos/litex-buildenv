#!/usr/bin/env python3
import os
from litex.gen.fhdl.structure import _Fragment

from opsis_base import *

from gateware.hdmi_in import HDMIIn


base_cls = MiniSoC

class VideoMixerSoC(base_cls):
        csr_peripherals = (
            "hdmi_in0",
            "hdmi_in0_edid_mem",
            "hdmi_in1",
            "hdmi_in1_edid_mem",
        )
        csr_map_update(base_cls.csr_map, csr_peripherals)

        interrupt_map = {
            "hdmi_in0": 3,
            "hdmi_in1": 4,
        }
        interrupt_map.update(base_cls.interrupt_map)

        def __init__(self, platform, **kwargs):
            base_cls.__init__(self, platform, **kwargs)
            self.submodules.hdmi_in0 = HDMIIn(platform.request("hdmi_in", 0),
                                              self.sdram.crossbar.get_master(),
                                              fifo_depth=512)
            self.submodules.hdmi_in1 = HDMIIn(platform.request("hdmi_in", 1),
                                              self.sdram.crossbar.get_master(),
                                              fifo_depth=512)


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = opsis_platform.Platform()
    soc = VideoMixerSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()
