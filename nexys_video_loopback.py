#!/usr/bin/env python3
import argparse
import os

from litex.gen import *
from litex.gen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.xilinx import VivadoProgrammer

from litex.boards.platforms import nexys_video

from litex.soc.integration.builder import *

from litevideo.input import HDMIIn
from litevideo.output.hdmi.s7 import S7HDMIOutPHY, S7HDMIOutEncoderSerializer


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk200 = ClockDomain()

        clk100 = platform.request("clk100")
        rst = platform.request("cpu_reset")

        pll_locked = Signal()
        pll_fb = Signal()
        pll_sys = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                # VCO @ 800 MHz
                p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                p_CLKFBOUT_MULT=8, p_DIVCLK_DIVIDE=1,
                i_CLKIN1=clk100, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                # 100 MHz
                p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0,
                o_CLKOUT0=pll_sys,

                # 200 MHz
                p_CLKOUT3_DIVIDE=4, p_CLKOUT3_PHASE=0.0,
                o_CLKOUT3=pll_clk200
            ),
            Instance("BUFG", i_I=pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked | rst),
        ]

        reset_counter = Signal(4, reset=15)
        ic_reset = Signal(reset=1)
        self.sync.clk200 += \
            If(reset_counter != 0,
                reset_counter.eq(reset_counter - 1)
            ).Else(
                ic_reset.eq(0)
            )
        self.specials += Instance("IDELAYCTRL", i_REFCLK=ClockSignal("clk200"), i_RST=ic_reset)


class HDMILoopback(Module):
    def __init__(self, platform):
        self.submodules.crg = _CRG(platform)

        hdmi_in_pads = platform.request("hdmi_in")

        # hdmi input
        default_edid = [
            0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00,
            0x04, 0x43, 0x07, 0xf2, 0x01, 0x00, 0x00, 0x00,
            0xff, 0x11, 0x01, 0x04, 0xa2, 0x4f, 0x00, 0x78,
            0x3e, 0xee, 0x91, 0xa3, 0x54, 0x4c, 0x99, 0x26,
            0x0f, 0x50, 0x54, 0x20, 0x00, 0x00, 0x01, 0x01,
            0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
            0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x02, 0x3a,
            0x80, 0x18, 0x71, 0x38, 0x2d, 0x40, 0x58, 0x2c,
            0x04, 0x05, 0x0f, 0x48, 0x42, 0x00, 0x00, 0x1e,
            0x01, 0x1d, 0x80, 0x18, 0x71, 0x1c, 0x16, 0x20,
            0x58, 0x2c, 0x25, 0x00, 0x0f, 0x48, 0x42, 0x00,
            0x00, 0x9e, 0x01, 0x1d, 0x00, 0x72, 0x51, 0xd0,
            0x1e, 0x20, 0x6e, 0x28, 0x55, 0x00, 0x0f, 0x48,
            0x42, 0x00, 0x00, 0x1e, 0x00, 0x00, 0x00, 0xfc,
            0x00, 0x48, 0x61, 0x6d, 0x73, 0x74, 0x65, 0x72,
            0x6b, 0x73, 0x0a, 0x20, 0x20, 0x20, 0x01, 0x74,
            0x02, 0x03, 0x18, 0x72, 0x47, 0x90, 0x85, 0x04,
            0x03, 0x02, 0x07, 0x06, 0x23, 0x09, 0x07, 0x07,
            0x83, 0x01, 0x00, 0x00, 0x65, 0x03, 0x0c, 0x00,
            0x10, 0x00, 0x8e, 0x0a, 0xd0, 0x8a, 0x20, 0xe0,
            0x2d, 0x10, 0x10, 0x3e, 0x96, 0x00, 0x1f, 0x09,
            0x00, 0x00, 0x00, 0x18, 0x8e, 0x0a, 0xd0, 0x8a,
            0x20, 0xe0, 0x2d, 0x10, 0x10, 0x3e, 0x96, 0x00,
            0x04, 0x03, 0x00, 0x00, 0x00, 0x18, 0x8e, 0x0a,
            0xa0, 0x14, 0x51, 0xf0, 0x16, 0x00, 0x26, 0x7c,
            0x43, 0x00, 0x1f, 0x09, 0x00, 0x00, 0x00, 0x98,
            0x8e, 0x0a, 0xa0, 0x14, 0x51, 0xf0, 0x16, 0x00,
            0x26, 0x7c, 0x43, 0x00, 0x04, 0x03, 0x00, 0x00,
            0x00, 0x98, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc9,
        ]
        #self.submodules.hdmi_in = HDMIIn(hdmi_in_pads, device="xc7", default_edid=default_edid)
        self.submodules.hdmi_in = HDMIIn(hdmi_in_pads, device="xc7")


        # hdmi output
        hdmi_out_pads = platform.request("hdmi_out")

        self.submodules.hdmi_output_clkgen = S7HDMIOutEncoderSerializer(hdmi_out_pads.clk_p, hdmi_out_pads.clk_n, bypass_encoder=True)
        self.submodules.hdmi_output = S7HDMIOutPHY(hdmi_out_pads)
        self.comb += [
                self.hdmi_output_clkgen.data.eq(Signal(10, reset=0b0000011111)),
                hdmi_out_pads.scl.eq(1)
        ]

        # hdmi loopback
        self.comb += [
            self.hdmi_output.sink.valid.eq(self.hdmi_in.syncpol.valid_o),
            self.hdmi_output.sink.de.eq(self.hdmi_in.syncpol.de),
            self.hdmi_output.sink.hsync.eq(self.hdmi_in.syncpol.hsync),
            self.hdmi_output.sink.vsync.eq(self.hdmi_in.syncpol.vsync),
            self.hdmi_output.sink.r.eq(self.hdmi_in.syncpol.r),
            self.hdmi_output.sink.g.eq(self.hdmi_in.syncpol.g),
            self.hdmi_output.sink.b.eq(self.hdmi_in.syncpol.b)
        ]


def main():
    platform = nexys_video.Platform()
    hdmi_loopback = HDMILoopback(platform)
    platform.build(hdmi_loopback)

    prog = VivadoProgrammer()
    prog.load_bitstream("build/top.bit")


if __name__ == "__main__":
    main()

