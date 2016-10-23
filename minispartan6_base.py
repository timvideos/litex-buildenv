#!/usr/bin/env python3

# Support for the MiniSpartan6+ - https://www.scarabhardware.com/minispartan6/
import argparse
import os
import struct
from fractions import Fraction
import importlib

from litex.gen import *
from litex.gen.fhdl.specials import Keep
from litex.gen.genlib.io import CRG
from litex.gen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.cores.flash import spi_flash
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.interconnect.csr import AutoCSR
from litex.soc.cores.uart.bridge import UARTWishboneBridge


from litedram.modules import AS4C16M16
from litedram.phy import gensdrphy
from litedram.core import ControllerSettings

import minispartan6_platform

from gateware import dna
from gateware import firmware

def csr_map_update(csr_map, csr_peripherals):
  csr_map.update(dict((n, v) for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))

class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()

        f0 = 32*1000000
        clk32 = platform.request("clk32")
        clk32a = Signal()
        self.specials += Instance("IBUFG", i_I=clk32, o_O=clk32a)
        clk32b = Signal()
        self.specials += Instance("BUFIO2", p_DIVIDE=1,
                                  p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
                                  i_I=clk32a, o_DIVCLK=clk32b)
        f = Fraction(int(clk_freq), int(f0))
        n, m, p = f.denominator, f.numerator, 8
        assert f0/n*m == clk_freq
        pll_lckd = Signal()
        pll_fb = Signal()
        pll = Signal(6)
        self.specials.pll = Instance("PLL_ADV", p_SIM_DEVICE="SPARTAN6",
                                     p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
                                     p_REF_JITTER=.01, p_CLK_FEEDBACK="CLKFBOUT",
                                     i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
                                     p_DIVCLK_DIVIDE=1, p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
                                     i_CLKIN1=clk32b, i_CLKIN2=0, i_CLKINSEL=1,
                                     p_CLKIN1_PERIOD=1000000000/f0, p_CLKIN2_PERIOD=0.,
                                     i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
                                     o_CLKOUT0=pll[0], p_CLKOUT0_DUTY_CYCLE=.5,
                                     o_CLKOUT1=pll[1], p_CLKOUT1_DUTY_CYCLE=.5,
                                     o_CLKOUT2=pll[2], p_CLKOUT2_DUTY_CYCLE=.5,
                                     o_CLKOUT3=pll[3], p_CLKOUT3_DUTY_CYCLE=.5,
                                     o_CLKOUT4=pll[4], p_CLKOUT4_DUTY_CYCLE=.5,
                                     o_CLKOUT5=pll[5], p_CLKOUT5_DUTY_CYCLE=.5,
                                     p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//1,
                                     p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//1,
                                     p_CLKOUT2_PHASE=0., p_CLKOUT2_DIVIDE=p//1,
                                     p_CLKOUT3_PHASE=0., p_CLKOUT3_DIVIDE=p//1,
                                     p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//1,  # sys
                                     p_CLKOUT5_PHASE=270., p_CLKOUT5_DIVIDE=p//1,  # sys_ps
        )
        self.specials += Instance("BUFG", i_I=pll[4], o_O=self.cd_sys.clk)
        self.specials += Instance("BUFG", i_I=pll[5], o_O=self.cd_sys_ps.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd)

        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=0, i_D1=1, i_S=0, i_R=0, i_CE=1,
                                  i_C0=self.cd_sys.clk, i_C1=~self.cd_sys.clk,
                                  o_Q=platform.request("sdram_clock"))

class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        "spiflash",
        "ddrphy",
        "dna",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "spiflash":     0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, **kwargs):
        clk_freq = 80*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            **kwargs)
        self.submodules.crg = _CRG(platform, clk_freq)
        self.submodules.dna = dna.DNA()

        self.submodules.spiflash = spi_flash.SpiFlash(
            platform.request("spiflash2x"), dummy=platform.spiflash_read_dummy_bits, div=platform.spiflash_clock_div)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size
        self.register_mem("spiflash", self.mem_map["spiflash"], self.spiflash.bus, size=platform.gateware_size)

        # sdram
        self.submodules.ddrphy = gensdrphy.GENSDRPHY(platform.request("sdram"))
        sdram_module = AS4C16M16(self.clk_freq, "1:1")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1/clk_freq*1e9)

def main():
    parser = argparse.ArgumentParser(description="Minispartan LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = minispartan6_platform.Platform()
    cls = BaseSoC
    builddir = "minispartan_base"
    output_dir=os.path.join("build", builddir)
    test_dir=os.path.join(output_dir, 'test')
    soc = cls(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir=os.path.join("build", builddir),
            compile_gateware = not args.nocompile_gateware,
            csr_csv=os.path.join(test_dir, 'csr.csv'))
    builder.add_software_package("libuip", "{}/firmware/libuip".format(os.getcwd()))
    builder.add_software_package("firmware", "{}/firmware".format(os.getcwd()))
    os.makedirs(test_dir) # FIXME: Remove when builder does this.
    vns = builder.build()

if __name__ == "__main__":
    main()
