#!/usr/bin/env python3
from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litescope import LiteScopeAnalyzer

from targets.opsis.net import csr_map_update
from targets.opsis.net import NetSoC


class VideoMixerSoC(NetSoC):
    csr_peripherals = (
        "hdmi_out0",
        "analyzer"
    )
    csr_map_update(NetSoC.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        NetSoC.__init__(self, platform, **kwargs)
        # hdmi out 0
        dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="pix", reverse=True)
        self.submodules.hdmi_out0 = VideoOut(platform.device,
                                            platform.request("hdmi_out", 0),
                                            dram_port,
                                            mode="ycbcr422",
                                            fifo_depth=4096)

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

        analyzer_signals = [
            #self.hdmi_out0.core.timing.hactive,
            #self.hdmi_out0.core.timing.vactive,
            #self.hdmi_out0.core.timing.active,
            #self.hdmi_out0.core.timing.hcounter,
            #self.hdmi_out0.core.timing.vcounter,
            self.hdmi_out0.core.timing.sink.valid,
            self.hdmi_out0.core.timing.sink.ready,
            self.hdmi_out0.core.timing.source.valid,
            self.hdmi_out0.core.timing.source.ready,

            #self.hdmi_out0.core.dma.offset,
            self.hdmi_out0.core.dma.sink.valid,
            self.hdmi_out0.core.dma.sink.ready,
            self.hdmi_out0.core.dma.source.valid,
            self.hdmi_out0.core.dma.source.ready,

            # FIXME: These don't seem to be valid anymore?
            #dram_port.counter,
            #dram_port.rdata_chunk,
            #dram_port.cmd_buffer.sink.valid,
            #dram_port.cmd_buffer.sink.ready,
            #dram_port.cmd_buffer.source.valid,
            #dram_port.cmd_buffer.source.ready,
            #dram_port.rdata_buffer.sink.valid,
            #dram_port.rdata_buffer.sink.ready,
            #dram_port.rdata_buffer.source.valid,
            #dram_port.rdata_buffer.source.ready,
            #dram_port.rdata_converter.sink.valid,
            #dram_port.rdata_converter.sink.ready,
            #dram_port.rdata_converter.source.valid,
            #dram_port.rdata_converter.source.ready,

        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 1024)

    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)


SoC = VideoMixerSoC
