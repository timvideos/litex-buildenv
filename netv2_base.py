#!/usr/bin/env python3
import argparse
import os

from litex.gen import *
from litex.gen.genlib.resetsync import AsyncResetSynchronizer

import netv2_platform as netv2

from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT41J128M16
from litedram.phy import a7ddrphy
from litedram.core import ControllerSettings
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker



class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()
        self.clock_domains.cd_clk100 = ClockDomain()
        self.clock_domains.cd_clk50 = ClockDomain()

        self.clock_domains.cd_clk125 = ClockDomain("clk125") # PCIe

        clk50 = platform.request("clk50")
        rst = Signal(reset=1) # FIXME

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_sys4x = Signal()
        pll_sys4x_dqs = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1600 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=20.0,
                     p_CLKFBOUT_MULT=32, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk50, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 100 MHz
                     p_CLKOUT0_DIVIDE=16, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

                     # 400 MHz
                     p_CLKOUT1_DIVIDE=4, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_sys4x,

                     # 400 MHz dqs
                     p_CLKOUT2_DIVIDE=4, p_CLKOUT2_PHASE=90.0,
                     o_CLKOUT2=pll_sys4x_dqs,

                     # 200 MHz
                     p_CLKOUT3_DIVIDE=8, p_CLKOUT3_PHASE=0.0,
                     o_CLKOUT3=pll_clk200,

                     # 400MHz
                     p_CLKOUT4_DIVIDE=4, p_CLKOUT4_PHASE=0.0,
                     #o_CLKOUT4=
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_clk100.clk),
            Instance("BUFG", i_I=pll_sys4x, o_O=self.cd_sys4x.clk),
            Instance("BUFG", i_I=pll_sys4x_dqs, o_O=self.cd_sys4x_dqs.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            Instance("BUFG", i_I=clk50, o_O=self.cd_clk50.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked | rst),
            AsyncResetSynchronizer(self.cd_clk100, ~pll_locked | rst),
            AsyncResetSynchronizer(self.cd_clk50, ~pll_locked | rst),
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


class BaseSoC(SoCSDRAM):
    csr_map = {
        "ddrphy":        17,
        "generator":     18,
        "checker":       19,
        "dna":           20,
        "xadc":          21,
        "pcie_phy":      22,
        "dma":           23,
        "msi":           24,
    }
    csr_map.update(SoCSDRAM.csr_map)

    def __init__(self, platform, **kwargs):
        clk_freq = 100*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            ident="NeTV2 LiteX Base SoC",
            **kwargs)

        self.submodules.crg = _CRG(platform)

        # sdram
        self.submodules.ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"))
        self.add_constant("A7DDRPHY_BITSLIP", 2)
        self.add_constant("A7DDRPHY_DELAY", 8)
        sdram_module = MT41J128M16(self.clk_freq, "1:4")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=ControllerSettings(with_bandwidth=True,
                                                                   cmd_buffer_depth=8,
                                                                   with_refresh=True))

        # sdram bist
        generator_port = self.sdram.crossbar.get_port(mode="write")
        self.submodules.generator = LiteDRAMBISTGenerator(generator_port)

        checker_port = self.sdram.crossbar.get_port(mode="read")
        self.submodules.checker = LiteDRAMBISTChecker(checker_port)

        # led blink
        counter = Signal(32)
        self.sync += counter.eq(counter + 1)
        self.comb += platform.request("user_led", 0).eq(counter[26])


def main():
    parser = argparse.ArgumentParser(description="NeTV2 LiteX Base SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    platform = netv2.Platform()
    soc = BaseSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build")
    vns = builder.build()


if __name__ == "__main__":
    main()
