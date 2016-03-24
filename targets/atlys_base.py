# Support for the Digilent Atlys board - digilentinc.com/atlys/
import math
import struct
from fractions import Fraction

from migen.fhdl.std import *
from migen.fhdl.specials import Keep
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.bus import wishbone
from migen.genlib.record import Record

from misoclib.mem.flash import spiflash
from misoclib.mem.sdram.module import P3R1GE4JGF
from misoclib.mem.sdram.phy import s6ddrphy
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.soc import mem_decoder
from misoclib.soc.sdram import SDRAMSoC

from liteeth.common import *
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.core.mac import LiteEthMAC

from gateware import dna
from gateware import firmware
from gateware import git_info
from gateware import platform_info

from targets.common import *


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        self.clock_domains.cd_base50 = ClockDomain()
        self.clock_domains.cd_encoder = ClockDomain()

        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # Input 100MHz clock
        f0 = 100*1000000
        clk100 = platform.request("clk100")
        clk100a = Signal()
        # Input 100MHz clock (buffered)
        self.specials += Instance("IBUFG", i_I=clk100, o_O=clk100a)
        clk100b = Signal()
        self.specials += Instance(
            "BUFIO2", p_DIVIDE=1,
            p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
            i_I=clk100a, o_DIVCLK=clk100b)

        f = Fraction(int(clk_freq), int(f0))
        n, m = f.denominator, f.numerator
        assert f0/n*m == clk_freq
        p = 8
        pll_lckd = Signal()
        pll_fb = Signal()

        unbuffered_sdram_full = Signal()
        unbuffered_sdram_half_a = Signal()
        unbuffered_sdram_half_b = Signal()
        unbuffered_encoder = Signal()
        unbuffered_sys = Signal()
        unbuffered_base50 = Signal()

        self.specials.pll = Instance(
            "PLL_ADV",
            p_SIM_DEVICE="SPARTAN6", p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
            p_REF_JITTER=.01,
            i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
            p_DIVCLK_DIVIDE=1,
            # Input Clocks (100MHz)
            i_CLKIN1=clk100b,
            p_CLKIN1_PERIOD=1e9/f0,
            i_CLKIN2=0,
            p_CLKIN2_PERIOD=0.,
            i_CLKINSEL=1,
            # Feedback
            i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
            p_CLK_FEEDBACK="CLKFBOUT",
            p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
            # (400MHz) sdram wr rd
            o_CLKOUT0=unbuffered_sdram_full, p_CLKOUT0_DUTY_CYCLE=.5,
            p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//4,
            # ( 66MHz) encoder
            o_CLKOUT1=unbuffered_encoder, p_CLKOUT1_DUTY_CYCLE=.5,
            p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=6,
            # (200MHz) sdram_half - sdram dqs adr ctrl
            o_CLKOUT2=unbuffered_sdram_half_a, p_CLKOUT2_DUTY_CYCLE=.5,
            p_CLKOUT2_PHASE=270., p_CLKOUT2_DIVIDE=p//2,
            # (200MHz) off-chip ddr
            o_CLKOUT3=unbuffered_sdram_half_b, p_CLKOUT3_DUTY_CYCLE=.5,
            p_CLKOUT3_PHASE=250., p_CLKOUT3_DIVIDE=p//2,
            # ( 50MHz) base50
            o_CLKOUT4=unbuffered_base50, p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//1,
            # ( 75MHz) sysclk
            o_CLKOUT5=unbuffered_sys, p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1.5,
        )
        # power on reset?
        reset = ~platform.request("cpu_reset")
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)

        # sys
        self.specials += Instance("BUFG", i_I=unbuffered_sys, o_O=self.cd_sys.clk)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))

        # base50
        self.specials += Instance("BUFG", i_I=unbuffered_base50, o_O=self.cd_base50.clk)

        # encoder
        self.specials += Instance("BUFG", i_I=unbuffered_encoder, o_O=self.cd_encoder.clk) # 66 MHz
        self.specials += AsyncResetSynchronizer(self.cd_encoder, self.cd_sys.rst)

        # SDRAM clocks
        # ------------------------------------------------------------------------------
        # sdram_full
        self.specials += Instance("BUFPLL", p_DIVIDE=4,
                                  i_PLLIN=unbuffered_sdram_full, i_GCLK=self.cd_sys.clk,
                                  i_LOCKED=pll_lckd, o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk4x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]
        # sdram_half
        self.specials += Instance("BUFG", i_I=unbuffered_sdram_half_a, o_O=self.cd_sdram_half.clk)
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", i_I=unbuffered_sdram_half_b, o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted, i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)

        #dcm_base50_locked = Signal()
        #self.specials += Instance("DCM_CLKGEN",
        #                          p_CLKFXDV_DIVIDE=2, p_CLKFX_DIVIDE=4, p_CLKFX_MD_MAX=1.0, p_CLKFX_MULTIPLY=2,
        #                          p_CLKIN_PERIOD=10.0, p_SPREAD_SPECTRUM="NONE", p_STARTUP_WAIT="FALSE",
        #
        #                          i_CLKIN=clk100a, o_CLKFX=self.cd_base50.clk,
        #                          o_LOCKED=dcm_base50_locked,
        #                          i_FREEZEDCM=0, i_RST=ResetSignal())
        #self.specials += AsyncResetSynchronizer(self.cd_base50, self.cd_sys.rst | ~dcm_base50_locked)


class BaseSoC(SDRAMSoC):
    default_platform = "atlys"

    csr_peripherals = (
        "spiflash",
        "ddrphy",
        "dna",
        "git_info",
        "platform_info",
    )
    csr_map_update(SDRAMSoC.csr_map, csr_peripherals)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
        "spiflash":     0x30000000,  # (default shadow @0xb0000000)
    }
    mem_map.update(SDRAMSoC.mem_map)

    def __init__(self, platform,
                 firmware_ram_size=0x10000,
                 firmware_filename=None,
                 **kwargs):
        clk_freq = 75*1000000
        SDRAMSoC.__init__(self, platform, clk_freq,
                          integrated_rom_size=0x8000,
                          sdram_controller_settings=LASMIconSettings(l2_size=32, with_bandwidth=True),
                          **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)
        self.submodules.dna = dna.DNA()
        self.submodules.git_info = git_info.GitInfo()
        self.submodules.platform_info = platform_info.PlatformInfo("atlys", self.__class__.__name__[:8])

        self.submodules.firmware_ram = firmware.FirmwareROM(firmware_ram_size, firmware_filename)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["firmware_ram"])

        if not self.integrated_main_ram_size:
            self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
                platform.request("ddram"),
                P3R1GE4JGF(self.clk_freq),
                rd_bitslip=0,
                wr_bitslip=4,
                dqs_ddr_alignment="C0",
            )
            self.comb += [
                self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
                self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
            ]
            self.register_sdram_phy(self.ddrphy)

        self.submodules.spiflash = spiflash.SpiFlash(
            platform.request("spiflash4x"), dummy=platform.spiflash_read_dummy_bits, div=platform.spiflash_clock_div)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size
        self.register_mem("spiflash", self.mem_map["spiflash"], self.spiflash.bus, size=platform.gateware_size)

        self.specials += Keep(self.crg.cd_sys.clk)
        self.specials += Keep(self.crg.cd_base50.clk)
        platform.add_platform_command("""
# Separate TMNs for FROM:TO TIG constraints
NET "{sys_clk}" TNM_NET = "TIGsys_clk";
NET "{base50_clk}" TNM_NET = "TIGbase50_clk";
""",
            sys_clk=self.crg.cd_sys.clk,
            base50_clk=self.crg.cd_base50.clk,
        )
        platform.add_period_constraint(self.crg.cd_sys.clk, math.floor(1e9/clk_freq))
        platform.add_period_constraint(self.crg.cd_base50.clk, 20) # 50 MHz


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
        "ethmac": 0x40000000,  # (shadow @0xc0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"), platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"]+self.shadow_base, 0x2000)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
# Separate TMNs for FROM:TO TIG constraints
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_rx_clk}" TNM_NET = "TIGeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "TIGeth_tx_clk";
TIMESPEC "TSeth_tx_to_sys" = FROM "TIGeth_tx_clk" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_tx" = FROM "TIGsys_clk" TO "TIGeth_tx_clk" TIG;
TIMESPEC "TSeth_rx_to_sys" = FROM "TIGeth_rx_clk" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_rx" = FROM "TIGsys_clk" TO "TIGeth_rx_clk" TIG;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)

default_subtarget = MiniSoC
