#!/usr/bin/env python3

from nexys_base import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litex.soc.cores.frequency_meter import FrequencyMeter

base_cls = MiniSoC


class VideoSoC(base_cls):
    csr_peripherals = {
        "hdmi_out",
        "hdmi_in",
        "hdmi_in_freq",
        "hdmi_in_edid_mem",
        "analyzer",
    }
    csr_map_update(base_cls.csr_map, csr_peripherals)

    interrupt_map = {
        "hdmi_in": 3,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, *args, **kwargs):
        base_cls.__init__(self, platform, *args, **kwargs)

        # # #

        pix_freq = 74.25e6

        # hdmi in
        hdmi_in_pads = platform.request("hdmi_in")
        self.submodules.hdmi_in_freq = FrequencyMeter(period=self.clk_freq)
        self.submodules.hdmi_in = HDMIIn(hdmi_in_pads,
                                         self.sdram.crossbar.get_port(mode="write"),
                                         fifo_depth=512,
                                         device="xc7")
        self.comb += [
            self.hdmi_in_freq.clk.eq(self.hdmi_in.clocking.cd_pix.clk),
            hdmi_in_pads.hpa.eq(1),
            hdmi_in_pads.txen.eq(1)
        ]
        self.platform.add_period_constraint(self.hdmi_in.clocking.cd_pix.clk, period_ns(1*pix_freq))
        self.platform.add_period_constraint(self.hdmi_in.clocking.cd_pix1p25x.clk, period_ns(1.25*pix_freq))
        self.platform.add_period_constraint(self.hdmi_in.clocking.cd_pix5x.clk, period_ns(5*pix_freq))

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_in.clocking.cd_pix.clk,
            self.hdmi_in.clocking.cd_pix1p25x.clk,
            self.hdmi_in.clocking.cd_pix5x.clk)

        # hdmi out
        hdmi_out_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="hdmi_out_pix", reverse=True)
        self.submodules.hdmi_out = VideoOut(platform.device,
                                            platform.request("hdmi_out"),
                                            hdmi_out_dram_port,
                                            "ycbcr422")

        self.platform.add_period_constraint(self.hdmi_out.driver.clocking.cd_pix.clk, period_ns(1*pix_freq))
        self.platform.add_period_constraint(self.hdmi_out.driver.clocking.cd_pix5x.clk, period_ns(5*pix_freq))

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out.driver.clocking.cd_pix.clk,
            self.hdmi_out.driver.clocking.cd_pix5x.clk)


def main():
    parser = argparse.ArgumentParser(description="Nexys LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = nexys_video.Platform()
    soc = VideoSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()

