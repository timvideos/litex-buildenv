#!/usr/bin/env python3
from opsis_base import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litedram.common import LiteDRAMPort
from litedram.frontend.adaptation import LiteDRAMPortCDC, LiteDRAMPortUpConverter

from litex.soc.cores.uart.bridge import UARTWishboneBridge

from litescope import LiteScopeAnalyzer

base_cls = BaseSoC


class VideoMixerSoC(base_cls):
    csr_peripherals = (
        "hdmi_out0",
        "hdmi_out1",
        "hdmi_in0",
        "hdmi_in0_edid_mem",
        "hdmi_in1",
        "hdmi_in1_edid_mem",
        "analyzer"
    )
    csr_map_update(base_cls.csr_map, csr_peripherals)

    interrupt_map = {
        "hdmi_in0": 3,
        "hdmi_in1": 4,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, **kwargs):
        base_cls.__init__(self, platform, **kwargs)
        hdmi_out0_crossbar_port_sys = self.sdram.crossbar.get_port()
        hdmi_out0_crossbar_port_pix = LiteDRAMPort(hdmi_out0_crossbar_port_sys.aw, hdmi_out0_crossbar_port_sys.dw, cd="pix")
        hdmi_out0_user_port_16_pix = LiteDRAMPort(hdmi_out0_crossbar_port_sys.aw, 16, cd="pix")

        port_converter = ClockDomainsRenamer("pix")(LiteDRAMPortUpConverter(hdmi_out0_user_port_16_pix, hdmi_out0_crossbar_port_pix))
        port_cdc = LiteDRAMPortCDC(hdmi_out0_crossbar_port_pix, hdmi_out0_crossbar_port_sys)
        self.submodules += port_converter, port_cdc

        self.submodules.hdmi_out0 = VideoOut(platform.device,
                                            platform.request("hdmi_out", 0),
                                            hdmi_out0_user_port_16_pix,
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
                pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk,
        )
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk)


        self.submodules.bridge = UARTWishboneBridge(self.platform.request("serial_debug"), self.clk_freq, baudrate=115200)
        self.add_wb_master(self.bridge.wishbone)

        if False:
            analyzer_signals = [
                self.hdmi_out0.core.initiator.source.valid,
                self.hdmi_out0.core.initiator.source.ready,
                self.hdmi_out0.core.initiator.source.hres,
                self.hdmi_out0.core.initiator.source.hsync_start,
                self.hdmi_out0.core.initiator.source.hsync_end,
                self.hdmi_out0.core.initiator.source.hscan,
                self.hdmi_out0.core.initiator.source.vres,
                self.hdmi_out0.core.initiator.source.vsync_start,
                self.hdmi_out0.core.initiator.source.vsync_end,
                self.hdmi_out0.core.initiator.source.vscan,
                self.hdmi_out0.core.initiator.source.base,
                self.hdmi_out0.core.initiator.source.end
            ]

        if False:
            analyzer_signals = [
                self.hdmi_out0.core.timing.source.valid,
                self.hdmi_out0.core.timing.source.ready,
                self.hdmi_out0.core.timing.source.de,
                self.hdmi_out0.core.timing.source.hsync,
                self.hdmi_out0.core.timing.source.vsync
            ]

        if False:
            analyzer_signals = [
                self.hdmi_out0.core.dma.source.valid,
                self.hdmi_out0.core.dma.source.ready,
                self.hdmi_out0.core.dma.source.data
            ]

        if False:
            analyzer_signals = [
                self.hdmi_out0.driver.sink.valid,
                self.hdmi_out0.driver.sink.de,
                self.hdmi_out0.driver.sink.hsync,
                self.hdmi_out0.driver.sink.vsync,
                self.hdmi_out0.driver.sink.r,
                self.hdmi_out0.driver.sink.g,
                self.hdmi_out0.driver.sink.b
            ]

        if True:
            analyzer_signals = [
                self.hdmi_out0.core.initiator.enable.storage,

                hdmi_out0_user_port_16_pix.cmd.valid,
                hdmi_out0_user_port_16_pix.cmd.ready,
                hdmi_out0_user_port_16_pix.cmd.we,
                hdmi_out0_user_port_16_pix.cmd.adr,

                hdmi_out0_user_port_16_pix.wdata.valid,
                hdmi_out0_user_port_16_pix.wdata.ready,
                #hdmi_out0_user_port_16_pix.wdata.data,
                hdmi_out0_user_port_16_pix.wdata.we,

                hdmi_out0_user_port_16_pix.rdata.valid,
                hdmi_out0_user_port_16_pix.rdata.ready,
                #hdmi_out0_user_port_16_pix.rdata.data,

                hdmi_out0_crossbar_port_sys.cmd.valid,
                hdmi_out0_crossbar_port_sys.cmd.ready,
                hdmi_out0_crossbar_port_sys.cmd.we,
                hdmi_out0_crossbar_port_sys.cmd.adr,

                hdmi_out0_crossbar_port_sys.wdata.valid,
                hdmi_out0_crossbar_port_sys.wdata.ready,
                #hdmi_out0_crossbar_port_sys.wdata.data,
                hdmi_out0_crossbar_port_sys.wdata.we,

                hdmi_out0_crossbar_port_sys.rdata.valid,
                hdmi_out0_crossbar_port_sys.rdata.ready,
                #hdmi_out0_crossbar_port_sys.rdata.data,

                #self.hdmi_out0.driver.sink.valid,
                #self.hdmi_out0.driver.sink.de,
                #self.hdmi_out0.driver.sink.hsync,
                #self.hdmi_out0.driver.sink.vsync


                self.hdmi_out0.core.source.valid,
                self.hdmi_out0.core.source.ready,
                self.hdmi_out0.core.source.de,
                self.hdmi_out0.core.source.hsync,
                self.hdmi_out0.core.source.vsync,
                #self.hdmi_out0.core.source.data,
                #self.hdmi_out0.driver.sink.de,
                #self.hdmi_out0.driver.sink.hsync,
                #self.hdmi_out0.driver.sink.vsync,
                self.ddrphy.dfi.phases[0].cas_n,
                self.ddrphy.dfi.phases[0].ras_n,
                self.ddrphy.dfi.phases[0].we_n,
                self.ddrphy.dfi.phases[0].cs_n,

                self.ddrphy.dfi.phases[1].cas_n,
                self.ddrphy.dfi.phases[1].ras_n,
                self.ddrphy.dfi.phases[1].we_n,
                self.ddrphy.dfi.phases[1].cs_n,

                self.ddrphy.dfi.phases[2].cas_n,
                self.ddrphy.dfi.phases[2].ras_n,
                self.ddrphy.dfi.phases[2].we_n,
                self.ddrphy.dfi.phases[2].cs_n,

                self.ddrphy.dfi.phases[3].cas_n,
                self.ddrphy.dfi.phases[3].ras_n,
                self.ddrphy.dfi.phases[3].we_n,
                self.ddrphy.dfi.phases[3].cs_n
            ]

        if False:
            analyzer_signals = [
                self.hdmi_out0.core.initiator.enable.storage,

                self.hdmi_out0.core.source.valid,
                self.hdmi_out0.core.source.ready,
                self.hdmi_out0.core.source.de,
                self.hdmi_out0.core.source.hsync,
                self.hdmi_out0.core.source.vsync,

                self.hdmi_out0.core.dma.address,
                self.hdmi_out0.core.dma.address_init,
                self.hdmi_out0.core.dma.address_inc,

                self.hdmi_out0.core.timing_done,
                self.hdmi_out0.core.dma_done,

                self.hdmi_out0.driver.sink.valid,
                self.hdmi_out0.driver.sink.de,
                self.hdmi_out0.driver.sink.hsync,
                self.hdmi_out0.driver.sink.vsync,

                self.hdmi_out0.core.dma.sink.ready,
                self.hdmi_out0.core.dma.sink.base,
                self.hdmi_out0.core.dma.sink.end,
            ]

        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048, cd="sys")


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
