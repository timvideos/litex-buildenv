# Support for the Numato Elbert v2
# XXX: Based on Numato Mimas v2 target, with DDR / SDRAM removed as 
# Numato Elbert v2 does not have external SDRAM (using SoCCore as a result).
#
# XXX: Completely untested at this stage!

import os

from fractions import Fraction

from litex.gen import *
from litex.gen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litedram.core import ControllerSettings

from gateware import info
from gateware import cas
from gateware import spi_flash

from targets.utils import csr_map_update


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        # Clock domains for the system (soft CPU and related components run at).
        self.clock_domains.cd_sys = ClockDomain()

        # Clock domain for peripherals (such as HDMI output).
        self.clock_domains.cd_base6 = ClockDomain()

        self.reset = Signal()

        # Input 12MHz clock
        f0 = 12*1000000
        clk12 = platform.request("clk12")
        clk12a = Signal()
        # Input 12MHz clock (buffered)
        self.specials += Instance("IBUFG", i_I=clk12, o_O=clk12a)
        clk12b = Signal()
        self.specials += Instance(
            "BUFIO2", p_DIVIDE=1,
            p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
            i_I=clk12a, o_DIVCLK=clk12b)

        p = 8
        f = Fraction(clk_freq*p, f0)
        n, d = f.numerator, f.denominator
        assert 19e6 <= f0/d <= 500e6  # pfd
        assert 400e6 <= f0*n/d <= 1080e6  # vco

        # Unbuffered output signals from the PLL. They need to be buffered
        # before feeding into the fabric.
        # XXX: We keep sdram clock signals to enable reuse of PLL config
        #      from Mimas v2
        unbuf_sdram_full = Signal()
        unbuf_unused = Signal()
        unbuf_sdram_half_a = Signal()
        unbuf_sdram_half_b = Signal()
        unbuf_sys = Signal()
        unbuf_periph = Signal()

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
            # Input Clocks (12MHz)
            i_CLKIN1=clk12b,
            p_CLKIN1_PERIOD=1e9/f0,
            i_CLKIN2=0,
            p_CLKIN2_PERIOD=0.,
            i_CLKINSEL=1,
            # Feedback
            i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
            p_CLK_FEEDBACK="CLKFBOUT",
            p_CLKFBOUT_MULT=n, p_CLKFBOUT_PHASE=0.,
            # (333MHz) sdram wr rd
            o_CLKOUT0=unbuf_sdram_full, p_CLKOUT0_DUTY_CYCLE=.5,
            p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//4,
            # unused?
            o_CLKOUT1=unbuf_unused, p_CLKOUT1_DUTY_CYCLE=.5,
            p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//4,
            # (???MHz) sdram_half - sdram dqs adr ctrl
            o_CLKOUT2=unbuf_sdram_half_a, p_CLKOUT2_DUTY_CYCLE=.5,
            p_CLKOUT2_PHASE=270., p_CLKOUT2_DIVIDE=p//2,
            # (????Hz) off-chip ddr
            o_CLKOUT3=unbuf_sdram_half_b, p_CLKOUT3_DUTY_CYCLE=.5,
            p_CLKOUT3_PHASE=270., p_CLKOUT3_DIVIDE=p//2,
            # ( 50MHz) periph
            o_CLKOUT4=unbuf_periph, p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//1,
            # ( ??MHz) sysclk
            o_CLKOUT5=unbuf_sys, p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,
        )


        # power on reset?
        reset = ~platform.request("user_btn", 5) | self.reset
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)

        # System clock - ??MHz
        self.specials += Instance("BUFG", name="sys_bufg", i_I=unbuf_sys, o_O=self.cd_sys.clk)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))

        # Peripheral clock - 6MHz (50%)
        # ------------------------------------------------------------------------------
        # The peripheral clock is kept separate from the system clock to allow
        # the system clock to be increased in the future.
        dcm_base6_locked = Signal()
        self.specials += [
            Instance("DCM_CLKGEN", name="crg_periph_dcm_clkgen",
                     p_CLKIN_PERIOD=10.0,
                     p_CLKFX_MULTIPLY=2,
                     p_CLKFX_DIVIDE=4,
                     p_CLKFX_MD_MAX=0.5, # CLKFX_MULTIPLY/CLKFX_DIVIDE
                     p_CLKFXDV_DIVIDE=2,
                     p_SPREAD_SPECTRUM="NONE",
                     p_STARTUP_WAIT="FALSE",

                     i_CLKIN=clk12a,
                     o_CLKFX=self.cd_base6.clk,
                     o_LOCKED=dcm_base6_locked,
                     i_FREEZEDCM=0,
                     i_RST=ResetSignal(),
                     ),
            AsyncResetSynchronizer(self.cd_base6,
                self.cd_sys.rst | ~dcm_base6_locked)
        ]
        platform.add_period_constraint(self.cd_base6.clk, 20)


class BaseSoC(SoCCore):
    csr_peripherals = (
        "spiflash",
        "info",
        "cas",
    )
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    mem_map = {
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, platform, **kwargs):

        cpu_reset_address = self.mem_map["spiflash"]+platform.gateware_size

        clk_freq = (83 + Fraction(1, 3))*1000*1000
        SoCCore.__init__(self, platform, clk_freq,
            #integrated_rom_size=0x8000,
            integrated_rom_size=None,
            integrated_sram_size=0x4000,
            uart_baudrate=19200,
            cpu_reset_address=cpu_reset_address,
            **kwargs)
        self.submodules.crg = _CRG(platform, clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        # Basic peripherals
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)

        # spi flash
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        bios_size = 0x8000
        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region("rom", cpu_reset_address, bios_size)
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size

SoC = BaseSoC
