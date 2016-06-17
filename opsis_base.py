#!/usr/bin/env python3

import argparse
import os
import struct
from fractions import Fraction
import importlib

from litex.gen import *
from litex.gen.fhdl.specials import Keep
from litex.gen.genlib.io import CRG
from litex.gen.genlib.resetsync import AsyncResetSynchronizer
from litex.gen.genlib.misc import WaitTimer


from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.interconnect.csr import AutoCSR
from litex.soc.cores.uart.bridge import UARTWishboneBridge


from litedram.modules import MT41J128M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

from liteeth.phy.s6rgmii import LiteEthPHYRGMII
from liteeth.core.mac import LiteEthMAC

import opsis_platform

from gateware import dna
from gateware import firmware


def csr_map_update(csr_map, csr_peripherals):
  csr_map.update(dict((n, v) for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


class FrontPanelGPIO(Module, AutoCSR):
    def __init__(self, platform, clk_freq):
        switches = Signal(1)
        leds = Signal(2)

        self.reset = Signal()

        # # #

        self.submodules.switches = GPIOIn(switches)
        self.submodules.leds = GPIOOut(leds)
        self.comb += [
           switches[0].eq(~platform.request("pwrsw")),
           platform.request("hdled").eq(~leds[0]),
           platform.request("pwled").eq(~leds[1]),
        ]

        # generate a reset when power switch is pressed for 1 second
        self.submodules.reset_timer = WaitTimer(clk_freq)
        self.comb += [
            self.reset_timer.wait.eq(switches[0]),
            self.reset.eq(self.reset_timer.done)
        ]


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys2x = ClockDomain()
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        self.clock_domains.cd_base50 = ClockDomain()

        self.clk8x_wr_strb = Signal()
        self.clk8x_rd_strb = Signal()

        self.reset = Signal()


        f0 = 100*1000000
        clk100 = platform.request("clk100")
        clk100a = Signal()
        self.specials += Instance("IBUFG", i_I=clk100, o_O=clk100a)
        clk100b = Signal()
        self.specials += Instance("BUFIO2", p_DIVIDE=1,
                                  p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
                                  i_I=clk100a, o_DIVCLK=clk100b)
        f = Fraction(int(clk_freq), int(f0))
        n, m = f.denominator, f.numerator
        assert f0/n*m == clk_freq
        p = 8
        pll_lckd = Signal()
        pll_fb = Signal()
        pll = Signal(6)
        self.specials.pll = Instance("PLL_ADV", p_SIM_DEVICE="SPARTAN6",
                                     p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
                                     p_REF_JITTER=.01, p_CLK_FEEDBACK="CLKFBOUT",
                                     i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
                                     p_DIVCLK_DIVIDE=1, p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
                                     i_CLKIN1=clk100b, i_CLKIN2=0, i_CLKINSEL=1,
                                     p_CLKIN1_PERIOD=1e9/f0, p_CLKIN2_PERIOD=0.,
                                     i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
                                     o_CLKOUT0=pll[0], p_CLKOUT0_DUTY_CYCLE=.5,
                                     o_CLKOUT1=pll[1], p_CLKOUT1_DUTY_CYCLE=.5,
                                     o_CLKOUT2=pll[2], p_CLKOUT2_DUTY_CYCLE=.5,
                                     o_CLKOUT3=pll[3], p_CLKOUT3_DUTY_CYCLE=.5,
                                     o_CLKOUT4=pll[4], p_CLKOUT4_DUTY_CYCLE=.5,
                                     o_CLKOUT5=pll[5], p_CLKOUT5_DUTY_CYCLE=.5,
                                     p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//8,    # sdram wr/rd full clock
                                     p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//8,    # unused
                                     p_CLKOUT2_PHASE=230., p_CLKOUT2_DIVIDE=p//4,  # sdram dqs adr ctrl off-chip
                                     p_CLKOUT3_PHASE=210., p_CLKOUT3_DIVIDE=p//4,  # ddr half clock
                                     p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//2,    # 2x system clock
                                     p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,    # system clock
        )
        self.specials += Instance("BUFG", i_I=pll[4], o_O=self.cd_sys2x.clk)
        self.specials += Instance("BUFG", i_I=pll[5], o_O=self.cd_sys.clk)
        reset = ~platform.request("cpu_reset") | self.reset
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)
        self.specials += AsyncResetSynchronizer(self.cd_sys2x, ~pll_lckd | (por > 0))
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))
        self.specials += Instance("BUFG", i_I=pll[2], o_O=self.cd_sdram_half.clk)
        self.specials += Instance("BUFPLL", p_DIVIDE=4,
                                  i_PLLIN=pll[0], i_GCLK=self.cd_sys2x.clk,
                                  i_LOCKED=pll_lckd, o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk8x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk8x_rd_strb.eq(self.clk8x_wr_strb),
        ]
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", i_I=pll[3], o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted, i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)


        dcm_base50_locked = Signal()
        self.specials += Instance("DCM_CLKGEN",
                                  p_CLKFXDV_DIVIDE=2, p_CLKFX_DIVIDE=4, p_CLKFX_MD_MAX=1.0, p_CLKFX_MULTIPLY=2,
                                  p_CLKIN_PERIOD=10.0, p_SPREAD_SPECTRUM="NONE", p_STARTUP_WAIT="FALSE",

                                  i_CLKIN=clk100a, o_CLKFX=self.cd_base50.clk,
                                  o_LOCKED=dcm_base50_locked,
                                  i_FREEZEDCM=0, i_RST=ResetSignal())
        self.specials += AsyncResetSynchronizer(self.cd_base50, self.cd_sys.rst | ~dcm_base50_locked)
        platform.add_period_constraint(self.cd_base50.clk, 20)

class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        "front_panel",
        "ddrphy",
        "dna",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform,
                 firmware_ram_size=0x10000,
                 firmware_filename="firmware/firmware.bin",
                 **kwargs):
        clk_freq = 50*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            **kwargs)
        self.submodules.crg = _CRG(platform, clk_freq)
        self.submodules.dna = dna.DNA()

        # front panel (ATX)
        self.submodules.front_panel = FrontPanelGPIO(platform, clk_freq)
        self.comb += self.crg.reset.eq(self.front_panel.reset)

        # firmware
        self.submodules.firmware_ram = firmware.FirmwareROM(firmware_ram_size, firmware_filename)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["firmware_ram"])

        # sdram
        self.submodules.ddrphy = s6ddrphy.S6QuarterRateDDRPHY(platform.request("ddram"),
                                                              rd_bitslip=0,
                                                              wr_bitslip=4,
                                                              dqs_ddr_alignment="C0")
        sdram_module = MT41J128M16(self.clk_freq, "1:4")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=ControllerSettings(with_bandwidth=True))
        self.comb += [
            self.ddrphy.clk8x_wr_strb.eq(self.crg.clk8x_wr_strb),
            self.ddrphy.clk8x_rd_strb.eq(self.crg.clk8x_rd_strb),
        ]

        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1/clk_freq*1e9)


class MiniSoC(BaseSoC):
    csr_peripherals = (
        "ethphy",
        "ethmac",
        "analyzer"
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    interrupt_map = {
        "ethmac": 2,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, *args, **kwargs):
        BaseSoC.__init__(self, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYRGMII(self.platform.request("eth_clocks"),
                                                 self.platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]

        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 8.0)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 8.0)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk,
            self.ethphy.crg.cd_eth_tx.clk)

        self.platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
PIN "BUFG_5.O" CLOCK_DEDICATED_ROUTE = FALSE;
""", eth_clocks_rx=self.platform.lookup_request("eth_clocks").rx)

def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--with-ethernet", action="store_true",
                        help="enable Ethernet support")
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = opsis_platform.Platform()
    cls = MiniSoC if args.with_ethernet else BaseSoC
    soc = cls(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()
