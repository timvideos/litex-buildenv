#!/usr/bin/env python3

from nexys_base import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litex.soc.cores.frequency_meter import FrequencyMeter

base_cls = MiniSoC


class VideoOutSoC(base_cls):
    csr_map = {
        "hdmi_out0": 21,
        "hdmi_in0": 22,
        "hdmi_in0_freq": 23,
        "hdmi_in0_edid_mem": 24,
        "analyzer": 25
    }
    csr_map.update(base_cls.csr_map)

    interrupt_map = {
        "hdmi_in0": 3,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, *args, **kwargs):
        base_cls.__init__(self, platform, *args, **kwargs)

        # # #

        # hdmi in 0
        hdmi_in0_pads = platform.request("hdmi_in", 0)
        self.submodules.hdmi_in0 = HDMIIn(hdmi_in0_pads,
                                          self.sdram.crossbar.get_port(mode="write"),
                                          fifo_depth=512,
                                          device="xc7")
        self.submodules.hdmi_in0_freq = FrequencyMeter(period=self.clk_freq)
        self.comb += [
            self.hdmi_in0_freq.clk.eq(self.hdmi_in0.clocking.cd_pix.clk),
            hdmi_in0_pads.hpa.eq(1),
            hdmi_in0_pads.txen.eq(1)
        ]
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix.clk, 13.4)
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix1p25x.clk, 10.8)
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix5x.clk, 2.6)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_in0.clocking.cd_pix.clk,
            self.hdmi_in0.clocking.cd_pix1p25x.clk,
            self.hdmi_in0.clocking.cd_pix5x.clk)

        # hdmi out 0
        hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="hdmi_out0_pix", reverse=True)
        self.submodules.hdmi_out0 = VideoOut(platform.device,
                                             platform.request("hdmi_out"),
                                             hdmi_out0_dram_port,
                                             "ycbcr422")

        self.platform.add_period_constraint(self.hdmi_out0.driver.clocking.cd_pix.clk, 13.4)
        self.platform.add_period_constraint(self.hdmi_out0.driver.clocking.cd_pix5x.clk, 2.6)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk,
            self.hdmi_out0.driver.clocking.cd_pix5x.clk)


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

