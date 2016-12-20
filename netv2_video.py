#!/usr/bin/env python3
import argparse
import os

from litex.gen import *
from litex.build.tools import write_to_file

import netv2_platform as netv2

from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import *
from litex.soc.interconnect.csr import *

from litevideo.output import VideoOut

from netv2_base import BaseSoC

import cpu_interface


class VideoSoC(BaseSoC):
    csr_map = {
        "hdmi_out0": 25,        
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self, platform, *args, **kw):
        BaseSoC.__init__(self, platform, *args, **kw)

        mode = "ycbcr422"
        if mode == "ycbcr422":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "ycbcr422")
        elif mode == "rgb":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=32, cd="pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "rgb")

#        self.platform.add_false_path_constraints(
#            self.crg.cd_sys.clk,
#            self.hdmi_out0.driver.clocking.cd_pix.clk)


def main():
    parser = argparse.ArgumentParser(description="NeTV2 LiteX PCIe SoC")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    platform = netv2.Platform()
    soc = VideoSoC(platform, **soc_core_argdict(args))
    builder = Builder(soc, output_dir="build")
    vns = builder.build()

    csr_header = cpu_interface.get_csr_header(soc.get_csr_regions(), soc.get_constants())
    write_to_file(os.path.join("software", "pcie", "kernel", "csr.h"), csr_header)

if __name__ == "__main__":
    main()
