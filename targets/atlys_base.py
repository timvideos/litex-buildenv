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
        # Clock domains for the system (soft CPU and related components run at).
        self.clock_domains.cd_sys = ClockDomain()
        # Clock domains for the DDR interface.
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        # Clock domain for peripherals (such as HDMI output).
        self.clock_domains.cd_periph = ClockDomain()
        # Clock domain for the JPEG Encoder.
        self.clock_domains.cd_encoder = ClockDomain()

        # Input 100MHz clock
        f0 = 100 * MHz
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

        # Unbuffered output signals from the PLL. They need to be buffered
        # before feeding into the fabric.
        unbuf_sdram_full = Signal()
        unbuf_sdram_half_a = Signal()
        unbuf_sdram_half_b = Signal()
        unbuf_encoder = Signal()
        unbuf_sys = Signal()
        unbuf_periph = Signal()

        # PLL signals
        pll_lckd = Signal()
        pll_fb = Signal()
        self.specials.pll = Instance(
            "PLL_ADV",
            p_SIM_DEVICE="SPARTAN6", p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
            p_REF_JITTER=.01,
            i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
            p_DIVCLK_DIVIDE=1,
            # Input Clocks (100MHz)
            i_CLKIN1=clk100b,
            p_CLKIN1_PERIOD=f0.to_ns(),
            i_CLKIN2=0,
            p_CLKIN2_PERIOD=0.,
            i_CLKINSEL=1,
            # Feedback
            i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
            p_CLK_FEEDBACK="CLKFBOUT",
            p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
            # (300MHz) sdram wr rd
            o_CLKOUT0=unbuf_sdram_full, p_CLKOUT0_DUTY_CYCLE=.5,
            p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//4,
            # ( 66MHz) encoder
            o_CLKOUT1=unbuf_encoder, p_CLKOUT1_DUTY_CYCLE=.5,
            p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=9,
            # (150MHz) sdram_half - sdram dqs adr ctrl
            o_CLKOUT2=unbuf_sdram_half_a, p_CLKOUT2_DUTY_CYCLE=.5,
            p_CLKOUT2_PHASE=270., p_CLKOUT2_DIVIDE=p//2,
            # (150MHz) off-chip ddr
            o_CLKOUT3=unbuf_sdram_half_b, p_CLKOUT3_DUTY_CYCLE=.5,
            p_CLKOUT3_PHASE=250., p_CLKOUT3_DIVIDE=p//2,
            # ( 50MHz) periph
            o_CLKOUT4=unbuf_periph, p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=12,
            # ( 75MHz) sysclk
            o_CLKOUT5=unbuf_sys, p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,
        )

        # assert the clocks turned out as requested.
        assert_pll_clock(300 * MHz, input=f0, feedback=(m*p//n), divide=(p//4), msg="CLKOUT0")
        assert_pll_clock( 66 * MHz, input=f0, feedback=(m*p//n), divide=(9   ), msg="CLKOUT1")
        assert_pll_clock(150 * MHz, input=f0, feedback=(m*p//n), divide=(p//2), msg="CLKOUT2 && CLKOUT3")
        assert_pll_clock( 50 * MHz, input=f0, feedback=(m*p//n), divide=(12  ), msg="CLKOUT4")
        assert_pll_clock( 75 * MHz, input=f0, feedback=(m*p//n), divide=(p//1), msg="CLKOUT5")

        # power on reset?
        reset = ~platform.request("cpu_reset")
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)

        # System clock - 75MHz
        self.specials += Instance("BUFG", i_I=unbuf_sys, o_O=self.cd_sys.clk)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))

        # Peripheral clock - 50MHz
        # The peripheral clock is kept separate from the system clock to allow
        # the system clock to be increased in the future.
        self.specials += Instance("BUFG", i_I=unbuf_periph, o_O=self.cd_periph.clk)
        self.specials += AsyncResetSynchronizer(self.cd_periph, self.cd_sys.rst)

        # JPEG encoder clock - 66MHz
        # The JPEG encoder has it's own clock as we want it to run at higher
        # speed then the other peripherals.
        self.specials += Instance("BUFG", i_I=unbuf_encoder, o_O=self.cd_encoder.clk)
        self.specials += AsyncResetSynchronizer(self.cd_encoder, self.cd_sys.rst)

        # SDRAM clocks
        # ------------------------------------------------------------------------------
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # sdram_full
        self.specials += Instance("BUFPLL", p_DIVIDE=4,
                                  i_PLLIN=unbuf_sdram_full, i_GCLK=self.cd_sys.clk,
                                  i_LOCKED=pll_lckd, o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk4x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]
        # sdram_half
        self.specials += Instance("BUFG", i_I=unbuf_sdram_half_a, o_O=self.cd_sdram_half.clk)
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", i_I=unbuf_sdram_half_b, o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted, i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)


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
        clk_freq = 75 * MHz
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
        self.specials += Keep(self.crg.cd_periph.clk)
        platform.add_platform_command("""
# Separate TMNs for FROM:TO TIG constraints
NET "{sys_clk}" TNM_NET = "TIGsys_clk";
NET "{periph_clk}" TNM_NET = "TIGperiph_clk";
NET "{encoder_clk}" TNM_NET = "TIGencoder_clk";

TIMESPEC "TSsys_to_periph" = FROM "TIGsys_clk" TO "TIGperiph_clk" TIG;
TIMESPEC "TSperiph_to_sys" = FROM "TIGperiph_clk" TO "TIGsys_clk" TIG;

TIMESPEC "TSsys_to_encoder" = FROM "TIGsys_clk" TO "TIGencoder_clk" TIG;
TIMESPEC "TSencoder_to_sys" = FROM "TIGencoder_clk" TO "TIGsys_clk" TIG;
""",
            sys_clk=self.crg.cd_sys.clk,
            periph_clk=self.crg.cd_periph.clk,
            encoder_clk=self.crg.cd_encoder.clk,
        )
        # These constraints are unneeded because ISE will trace through the PLL
        # block and calculate them.
        #platform.add_period_constraint(self.crg.cd_sys.clk, 13) # 13.33ns == 75 MHz
        #platform.add_period_constraint(self.crg.cd_periph.clk, 20) # 20ns == 50 MHz


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
NET "{eth_clocks_rx}" TNM_NET = "TIGeth_clocks_rx";
TIMESPEC "TSeth_clocks_rx_to_sys" = FROM "TIGeth_clocks_rx" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_clocks_rx" = FROM "TIGsys_clk" TO "TIGeth_clocks_rx" TIG;

NET "{eth_clocks_tx}" TNM_NET = "TIGeth_clocks_tx";
TIMESPEC "TSeth_clocks_tx_to_sys" = FROM "TIGeth_clocks_tx" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_clocks_tx" = FROM "TIGsys_clk" TO "TIGeth_clocks_tx" TIG;

#NET "{eth_rx_clk}" TNM_NET = "TIGeth_rx_clk";
#TIMESPEC "TSeth_rx_to_sys" = FROM "TIGeth_rx_clk" TO "TIGsys_clk" TIG;
#TIMESPEC "TSsys_to_eth_rx" = FROM "TIGsys_clk" TO "TIGeth_rx_clk" TIG;

#NET "{eth_tx_clk}" TNM_NET = "TIGeth_tx_clk";
#TIMESPEC "TSeth_tx_to_sys" = FROM "TIGeth_tx_clk" TO "TIGsys_clk" TIG;
#TIMESPEC "TSsys_to_eth_tx" = FROM "TIGsys_clk" TO "TIGeth_tx_clk" TIG;
""",
            eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
            eth_clocks_tx=platform.lookup_request("eth_clocks").tx,
            eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
            eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk,
        )


default_subtarget = BaseSoC
