#!/usr/bin/env python3
from opsis_base import *

from litex.soc.cores.uart.bridge import UARTWishboneBridge

from litevideo.output import VideoOut

from litescope import LiteScopeAnalyzer

base_cls = BaseSoC


class VideoMixerSoC(base_cls):
    csr_peripherals = (
        "hdmi_out0",
        "hdmi_out1",
        "analyzer"
    )
    csr_map_update(base_cls.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        base_cls.__init__(self, platform, **kwargs)
        # hdmi out 0
        hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="pix", reverse=True)
        self.submodules.hdmi_out0 = VideoOut(platform.device,
                                            platform.request("hdmi_out", 0),
                                            hdmi_out0_dram_port,
                                            "ycbcr422")

        # all PLL_ADV are used: router needs help...
        platform.add_platform_command("""INST PLL_ADV LOC=PLL_ADV_X0Y0;""")
        # FIXME: Fix the HDMI out so this can be removed.
        platform.add_platform_command(
            """PIN "hdmi_out_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command(
            """
NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
""",
                pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk
        )
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk)

        self.submodules.bridge = UARTWishboneBridge(self.platform.request("serial_debug"), self.clk_freq, baudrate=115200)
        self.add_wb_master(self.bridge.wishbone)

        analyzer_signals = [
            self.hdmi_out0.core.dma.reader.sink.valid,
            self.hdmi_out0.core.dma.reader.sink.ready,
            self.hdmi_out0.core.dma.reader.sink.address,

            self.hdmi_out0.core.dma.reader.source.valid,
            self.hdmi_out0.core.dma.reader.source.ready,
            self.hdmi_out0.core.dma.reader.source.data,

            self.hdmi_out0.core.source.valid,
            self.hdmi_out0.core.source.ready,
            self.hdmi_out0.core.source.de,
            self.hdmi_out0.core.source.hsync,
            self.hdmi_out0.core.source.vsync,
            self.hdmi_out0.core.source.data
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048, cd="pix", cd_ratio=2)


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
    soc.analyzer.export_csv(vns, "test/analyzer.csv")

if __name__ == "__main__":
    main()
