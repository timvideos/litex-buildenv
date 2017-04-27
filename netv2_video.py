#!/usr/bin/env python3

from netv2_base import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut
from litedram.common import LiteDRAMPort

base_cls = BaseSoC


class VideoOutSoC(base_cls):
    csr_map = {
        "hdmi_out": 26,
        "hdmi_in": 27,
        "hdmi_in_edid_mem": 28,
    }
    csr_map.update(base_cls.csr_map)

    interrupt_map = {
        "hdmi_in": 3,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, *args, **kwargs):
        base_cls.__init__(self, platform, *args, pcie_blink=False, **kwargs)

        # # #

        # hdmi in
        self.submodules.hdmi_in = HDMIIn(platform.request("hdmi_in", 0),
                                         self.sdram.crossbar.get_port(mode="write"),
                                         fifo_depth=512,
                                         device="xc7")

        # hdmi out
        hdmi_out_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="hdmi_out_pix", reverse=True)
        self.submodules.hdmi_out = VideoOut(platform.device,
                                            platform.request("hdmi_out"),
                                            hdmi_out_dram_port,
                                            "ycbcr422")

        self.platform.add_period_constraint(self.crg.cd_sys.clk, 10.0)
        self.platform.add_period_constraint(self.hdmi_out.driver.clocking.cd_pix.clk, 10.0)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out.driver.clocking.cd_pix.clk)


def main():
    parser = argparse.ArgumentParser(description="NeTV2 LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    platform = netv2.Platform()
    soc = VideoOutSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build")
    vns = builder.build()

if __name__ == "__main__":
    main()
