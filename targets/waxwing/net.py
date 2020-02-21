# Support for the Numato Saturn (http://numato.com/product/saturn-spartan-6-fpga-development-board-with-ddr-sdram)
# Original code from : https://github.com/timvideos/litex-buildenv/blob/master/targets/waxwing/base.py
# By Rohit Singh

from fractions import Fraction

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import *

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT46H32M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

from targets.utils import csr_map_update, dict_set_max
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.mac import LiteEthMAC

from litex.soc.interconnect import wishbone

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, clk_freq):
        # Clock domains for the system (soft CPU and related components run at).
        self.clock_domains.cd_sys = ClockDomain()
        # Clock domains for the DDR interface.
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        self.clock_domains.cd_eth = ClockDomain()

        # Input 100MHz clock
        f0 = Fraction(100, 1)*1000000
        clk100 = platform.request("clk100")
        clk100a = Signal()
        # Input 100MHz clock (buffered)
        self.specials += Instance(
            "IBUFG",
            i_I=clk100,
            o_O=clk100a
        )

        clk100b = Signal()

        self.specials += Instance(
            "BUFIO2",
            p_DIVIDE=1,
            p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
            i_I=clk100a,
            o_DIVCLK=clk100b
        )

        #PLL parameters
        f = Fraction(10, 1)
        n, d = f.numerator, f.denominator
        p = 8

        assert f0*n/d/p/4 == clk_freq
        assert 19e6     <= f0/d     <= 500e6    # pfd
        assert 400e6    <= f0*n/d   <= 1000e6   # vco

        # Unbuffered output signals from the PLL. They need to be buffered
        # before feeding into the fabric.
        unbuf_sdram_full    = Signal()
        unbuf_sdram_half_a  = Signal()
        unbuf_sdram_half_b  = Signal()
        unbuf_unused_a      = Signal()
        unbuf_eth           = Signal()
        unbuf_sys           = Signal()

        # PLL signals
        pll_lckd = Signal()
        pll_fb = Signal()
        self.specials.pll = Instance(
            "PLL_ADV",
            name="crg_pll_adv",
            p_SIM_DEVICE="SPARTAN6", p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
            p_REF_JITTER=.01,
            i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
            p_DIVCLK_DIVIDE=d,
            # Input Clocks (100MHz)
            i_CLKIN1=clk100b,
            p_CLKIN1_PERIOD=1e9/f0,
            i_CLKIN2=0,
            p_CLKIN2_PERIOD=0.,
            i_CLKINSEL=1,
            # Feedback
            i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
            p_CLK_FEEDBACK="CLKFBOUT",
            p_CLKFBOUT_MULT=n, p_CLKFBOUT_PHASE=0.,
            # Outputs
            # (125 MHz) sdram wr rd
            o_CLKOUT0=unbuf_sdram_full,   p_CLKOUT0_DUTY_CYCLE=.5,
            p_CLKOUT0_PHASE=0.,   p_CLKOUT0_DIVIDE=p,
            # (125 MHz) unused
            o_CLKOUT1=unbuf_unused_a,     p_CLKOUT1_DUTY_CYCLE=.5,
            p_CLKOUT1_PHASE=0.,   p_CLKOUT1_DIVIDE=p,
            # (62.5 MHz) sdram_half - sdram dqs adr ctrl
            o_CLKOUT2=unbuf_sdram_half_a, p_CLKOUT2_DUTY_CYCLE=.5,
            p_CLKOUT2_PHASE=270., p_CLKOUT2_DIVIDE=(p*2),
            # (62.5 MHz) off-chip ddr
            o_CLKOUT3=unbuf_sdram_half_b, p_CLKOUT3_DUTY_CYCLE=.5,
            p_CLKOUT3_PHASE=270., p_CLKOUT3_DIVIDE=(p*2),
            # (25.00 MHz) eth
            o_CLKOUT4=unbuf_eth,  p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0.,   p_CLKOUT4_DIVIDE=(p*5),
            # (31.25 MHz) sysclk
            o_CLKOUT5=unbuf_sys,          p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0.,   p_CLKOUT5_DIVIDE=(p*4),
        )

        #power on reset?
        reset = ~platform.request("user_btn", 0)
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)

        #System clock
        self.specials += Instance("BUFG", i_I=unbuf_sys, o_O=self.cd_sys.clk)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))

        # SDRAM clocks
        # ------------------------------------------------------------------------------
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # sdram_full
        self.specials += Instance(
            "BUFPLL",
            p_DIVIDE=4,
            i_PLLIN=unbuf_sdram_full,
            i_GCLK=self.cd_sys.clk,
            i_LOCKED=pll_lckd,
            o_IOCLK=self.cd_sdram_full_wr.clk,
            o_SERDESSTROBE=self.clk4x_wr_strb
        )

        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]

        # ethernet
        self.specials += Instance(
            "BUFG",
            i_I=unbuf_eth,
            o_O=self.cd_eth.clk
        )

        # sdram_half
        self.specials += Instance(
            "BUFG",
            i_I=unbuf_sdram_half_a,
            o_O=self.cd_sdram_half.clk
        )

        clk_sdram_half_shifted = Signal()
        self.specials += Instance(
            "BUFG",
            i_I=unbuf_sdram_half_b,
            o_O=clk_sdram_half_shifted
        )

        clk = platform.request("ddram_clock")
        self.specials += Instance(
            "ODDR2",
            p_DDR_ALIGNMENT="NONE",
            p_INIT=0, p_SRTYPE="SYNC",
            i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
            i_C0=clk_sdram_half_shifted,
            i_C1=~clk_sdram_half_shifted,
            o_Q=clk.p
        )

        self.specials += Instance(
            "ODDR2",
            p_DDR_ALIGNMENT="NONE",
            p_INIT=0, p_SRTYPE="SYNC",
            i_D0=0, i_D1=1, i_S=0, i_R=0, i_CE=1,
            i_C0=clk_sdram_half_shifted,
            i_C1=~clk_sdram_half_shifted,
            o_Q=clk.n
        )

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
    mem_map = {
        "emulator_ram": 0x50000000,  # (default shadow @0xd0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, **kwargs):
        dict_set_max(kwargs, 'integrated_rom_size', 0x8000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x8000)

        clk_freq = (31 + Fraction(1, 4))*1000*1000
        SoCSDRAM.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)

        if self.cpu_type == "vexriscv" and self.cpu_variant == "linux":
            size = 0x4000
            self.submodules.emulator_ram = wishbone.SRAM(size)
            self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, size)

        # sdram
        if not self.integrated_main_ram_size:        
            sdram_module = MT46H32M16(clk_freq, "1:2")
            self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
                platform.request("ddram"),
                sdram_module.memtype,
                rd_bitslip=2,
                wr_bitslip=3,
                dqs_ddr_alignment="C1"
            )
            self.add_csr("ddrphy")

            self.register_sdram(self.ddrphy,
                sdram_module.geom_settings,
                sdram_module.timing_settings,
                controller_settings=ControllerSettings(
                    with_bandwidth=True)
            )

            self.comb += [
                self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
                self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
            ]

# EthernetSoC --------------------------------------------------------------------------------------

class EthernetSoC(BaseSoC):
    mem_map = {
        "ethmac": 0xb0000000,
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, *args, **kwargs):
        # Need a larger integrated ROM on or1k to fit the BIOS with TFTP support.
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size'] = 0x10000
        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYMII(self.platform.request("eth_clocks"),
                                               self.platform.request("eth"))
        self.add_csr("ethphy")
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
            interface="wishbone", endianness=self.cpu.endianness)
        self.add_wb_slave(self.mem_map["ethmac"], self.ethmac.bus, 0x2000)
        self.add_memory_region("ethmac", self.mem_map["ethmac"], 0x2000, type="io")
        self.add_csr("ethmac")
        self.add_interrupt("ethmac")
        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        #self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 1e9/12.5e6)
        #self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 1e9/12.5e6)
        #self.platform.add_false_path_constraints(
        #    self.crg.cd_sys.clk,
        #    self.ethphy.crg.cd_eth_rx.clk,
        #    self.ethphy.crg.cd_eth_tx.clk)

SoC = EthernetSoC
