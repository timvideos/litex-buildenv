#!/usr/bin/env python3

from nexys_etherbone import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litescope import LiteScopeAnalyzer

from gateware.freq_measurement import FrequencyMeasurement

base_cls = EtherboneSoC


class VideoOutSoC(base_cls):
    csr_map = {
        "hdmi_in": 22,
        "hdmi_in_freq": 23,
        "hdmi_in_edid_mem": 24,
        "analyzer": 25
    }
    csr_map.update(base_cls.csr_map)

    interrupt_map = {
        "hdmi_in": 3,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, *args, **kwargs):
        base_cls.__init__(self, platform, *args, **kwargs)

        # # #

        # hdmi in
        self.submodules.hdmi_in = HDMIIn(platform.request("hdmi_in", 0),
                                         None,
                                         fifo_depth=512,
                                         device="xc7",)
        self.submodules.hdmi_in_freq = FrequencyMeasurement(self.hdmi_in.clocking.cd_pix.clk,
                                                            self.clk_freq)


        analyzer_signals = [
            self.hdmi_in.data0_cap.alignment.delay_value,
            self.hdmi_in.data0_cap.alignment.delay_ce,
            self.hdmi_in.data0_cap.alignment.bitslip_value,
            self.hdmi_in.data0_cap.alignment.invalid,
            self.hdmi_in.data0_cap.d,

            self.hdmi_in.data1_cap.alignment.delay_value,
            self.hdmi_in.data1_cap.alignment.delay_ce,
            self.hdmi_in.data1_cap.alignment.bitslip_value,
            self.hdmi_in.data1_cap.alignment.invalid,
            self.hdmi_in.data1_cap.d,

            self.hdmi_in.data2_cap.alignment.delay_value,
            self.hdmi_in.data2_cap.alignment.delay_ce,
            self.hdmi_in.data2_cap.alignment.bitslip_value,
            self.hdmi_in.data2_cap.alignment.invalid,
            self.hdmi_in.data2_cap.d,

            self.hdmi_in.syncpol.valid_o,
            self.hdmi_in.syncpol.de,
            self.hdmi_in.syncpol.hsync,
            self.hdmi_in.syncpol.vsync,
            self.hdmi_in.syncpol.r,
            self.hdmi_in.syncpol.g,
            self.hdmi_in.syncpol.b,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048, cd="pix")

    def do_exit(self, vns):
        self.analyzer.export_csv(vns, "test/analyzer.csv")


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

