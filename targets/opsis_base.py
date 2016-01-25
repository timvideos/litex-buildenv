# Support for the Numato Opsis - The first HDMI2USB production board
import struct
from fractions import Fraction

from migen.fhdl.std import *
from migen.fhdl.specials import Keep
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.bus import wishbone
from migen.genlib.record import Record

from misoclib.com import gpio
from misoclib.mem.sdram.module import MT41J128M16
from misoclib.mem.sdram.phy import s6ddrphy
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.soc import mem_decoder
from misoclib.soc.sdram import SDRAMSoC

from liteeth.phy.s6rgmii import LiteEthPHYRGMII
from liteeth.core.mac import LiteEthMAC

from gateware import dna
from gateware import i2c
from gateware import i2c_hack
from targets.common import *


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys2x = ClockDomain()
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        self.clock_domains.cd_base50 = ClockDomain()
        self.clock_domains.cd_encoder = ClockDomain()

        self.clk8x_wr_strb = Signal()
        self.clk8x_rd_strb = Signal()

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
                                     p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//8,  # sdram wr rd
                                     p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//8,
                                     p_CLKOUT2_PHASE=230., p_CLKOUT2_DIVIDE=p//4,  # sdram dqs adr ctrl
                                     p_CLKOUT3_PHASE=210., p_CLKOUT3_DIVIDE=p//4,  # off-chip ddr
                                     p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//2,
                                     p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,  # sys
        )
        self.specials += Instance("BUFG", i_I=pll[4], o_O=self.cd_sys2x.clk)
        self.specials += Instance("BUFG", i_I=pll[5], o_O=self.cd_sys.clk)
        reset = ~platform.request("cpu_reset")
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

        self.comb += self.cd_encoder.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_encoder, self.cd_sys.rst)


class BaseSoC(SDRAMSoC):
    default_platform = "opsis"

    csr_peripherals = (
        "ddrphy",
        "dna",
        "fx2_reset",
        "fx2_hack",
#        "opsis_eeprom_i2c",
        "tofe_eeprom_i2c",
    )
    csr_map_update(SDRAMSoC.csr_map, csr_peripherals)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SDRAMSoC.mem_map)

    def __init__(self, platform,
                 firmware_ram_size=0x10000,
                 firmware_filename=None,
                 **kwargs):
        clk_freq = 50*1000000
        SDRAMSoC.__init__(self, platform, clk_freq,
                          integrated_rom_size=0x8000,
                          sdram_controller_settings=LASMIconSettings(l2_size=32, with_bandwidth=True),
                          **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)
        self.submodules.dna = dna.DNA()
#        self.submodules.opsis_eeprom_i2c = i2c.I2C(platform.request("opsis_eeprom"))
        self.submodules.fx2_reset = gpio.GPIOOut(platform.request("fx2_reset"))
        self.submodules.fx2_hack = i2c_hack.I2CShiftReg(platform.request("opsis_eeprom"))

        self.submodules.tofe_eeprom_i2c = i2c.I2C(platform.request("tofe_eeprom"))

        self.submodules.firmware_ram = wishbone.SRAM(firmware_ram_size, init=get_firmware_data(firmware_filename))
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["firmware_ram"])

        if not self.integrated_main_ram_size:
            self.submodules.ddrphy = s6ddrphy.S6QuarterRateDDRPHY(platform.request("ddram"),
                                                                  MT41J128M16(self.clk_freq),
                                                                  rd_bitslip=0,
                                                                  wr_bitslip=4,
                                                                  dqs_ddr_alignment="C0")
            self.comb += [
                self.ddrphy.clk8x_wr_strb.eq(self.crg.clk8x_wr_strb),
                self.ddrphy.clk8x_rd_strb.eq(self.crg.clk8x_rd_strb),
            ]
            self.register_sdram_phy(self.ddrphy)

        self.specials += Keep(self.crg.cd_sys.clk)
        platform.add_platform_command("""
NET "{sys_clk}" TNM_NET = "GRPsys_clk";
""", sys_clk=self.crg.cd_sys.clk)


class MiniSoC(BaseSoC):
    csr_peripherals = (
        "ethphy",
        "ethmac",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    interrupt_map = {
        "ethmac": 2,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.ethphy = LiteEthPHYRGMII(platform.request("eth_clocks"), platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"]+self.shadow_base, 0x2000)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_rx_clk}" TNM_NET = "GRPeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "GRPeth_tx_clk";
TIMESPEC "TSise_sucks1" = FROM "GRPeth_tx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks2" = FROM "GRPsys_clk" TO "GRPeth_tx_clk" TIG;
TIMESPEC "TSise_sucks3" = FROM "GRPeth_rx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks4" = FROM "GRPsys_clk" TO "GRPeth_rx_clk" TIG;
PIN "BUFG_4.O" CLOCK_DEDICATED_ROUTE = FALSE;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)

default_subtarget = BaseSoC
