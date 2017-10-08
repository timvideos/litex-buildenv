#!/usr/bin/env python3

from nexys_base import *

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from litex.soc.cores.frequency_meter import FrequencyMeter

from litescope import LiteScopeAnalyzer


class VideoSoC(BaseSoC):
    csr_peripherals = {
        "hdmi_out0",
        "hdmi_in0",
        "hdmi_in0_freq",
        "hdmi_in0_edid_mem",
    }
    csr_map_update(base_cls.csr_map, csr_peripherals)

    interrupt_map = {
        "hdmi_in0": 3,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)


        pix_freq = 148.50e6

        # hdmi in
        hdmi_in0_pads = platform.request("hdmi_in")
        self.submodules.hdmi_in0_freq = FrequencyMeter(period=self.clk_freq)
        self.submodules.hdmi_in0 = HDMIIn(hdmi_in0_pads,
                                          self.sdram.crossbar.get_port(mode="write"),
                                          fifo_depth=512,
                                          device="xc7")
        self.comb += [
            self.hdmi_in0_freq.clk.eq(self.hdmi_in0.clocking.cd_pix.clk),
            hdmi_in0_pads.txen.eq(1)
        ]
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix.clk, period_ns(1*pix_freq))
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix1p25x.clk, period_ns(1.25*pix_freq))
        self.platform.add_period_constraint(self.hdmi_in0.clocking.cd_pix5x.clk, period_ns(5*pix_freq))

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_in0.clocking.cd_pix.clk,
            self.hdmi_in0.clocking.cd_pix1p25x.clk,
            self.hdmi_in0.clocking.cd_pix5x.clk)

        # hdmi out
        mode = "ycbcr422"
        if mode == "ycbcr422":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="hdmi_out0_pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "ycbcr422",
                                                 fifo_depth=4096)
        elif mode == "rgb":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=32, cd="hdmi_out0_pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "rgb",
                                                 fifo_depth=4096)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk)

        self.platform.add_period_constraint(self.hdmi_out0.driver.clocking.cd_pix.clk, period_ns(1*pix_freq))
        self.platform.add_period_constraint(self.hdmi_out0.driver.clocking.cd_pix5x.clk, period_ns(5*pix_freq))

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk,
            self.hdmi_out0.driver.clocking.cd_pix5x.clk)

        # hdmi over
        self.comb += [
            platform.request("hdmi_sda_over_up").eq(0),
            platform.request("hdmi_sda_over_dn").eq(0),
            platform.request("hdmi_hdp_over").eq(0),
        ]


class VideoSoCDebug(VideoSoC):
    csr_peripherals = {
        "analyzer",
    }
    csr_map_update(VideoSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        VideoSoC.__init__(self, platform, *args, **kwargs)

        # # #

        # analyzer
        analyzer_signals = [
            self.hdmi_in0.data0_charsync.raw_data,
            self.hdmi_in0.data1_charsync.raw_data,
            self.hdmi_in0.data2_charsync.raw_data,

            self.hdmi_in0.data0_charsync.synced,
            self.hdmi_in0.data1_charsync.synced,
            self.hdmi_in0.data2_charsync.synced,

            self.hdmi_in0.data0_charsync.data,
            self.hdmi_in0.data1_charsync.data,
            self.hdmi_in0.data2_charsync.data,

            self.hdmi_in0.syncpol.valid_o,
            self.hdmi_in0.syncpol.de,
            self.hdmi_in0.syncpol.hsync,
            self.hdmi_in0.syncpol.vsync,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 1024, cd="hdmi_in0_pix", cd_ratio=2)

        # leds
        pix_counter = Signal(32)
        self.sync.hdmi_in0_pix += pix_counter.eq(pix_counter + 1)
        self.comb += platform.request("user_led", 0).eq(pix_counter[26])

        pix1p25x_counter = Signal(32)
        self.sync.pix1p25x += pix1p25x_counter.eq(pix1p25x_counter + 1)
        self.comb += platform.request("user_led", 1).eq(pix1p25x_counter[26])

        pix5x_counter = Signal(32)
        self.sync.hdmi_in0_pix5x += pix5x_counter.eq(pix5x_counter + 1)
        self.comb += platform.request("user_led", 2).eq(pix5x_counter[26])


    def do_exit(self, vns):
        self.analyzer.export_csv(vns, "test/analyzer.csv")


SoC = VideoSoC
