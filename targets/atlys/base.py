# Support for the Digilent Atlys board - digilentinc.com/atlys/
from fractions import Fraction

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.genlib.misc import WaitTimer

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import P3R1GE4JGF
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

#from gateware import cas
from gateware import info
from gateware import spi_flash

from targets.utils import csr_map_update


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        # Clock domains for the system (soft CPU and related components run at).
        self.clock_domains.cd_sys = ClockDomain()
        # Clock domains for the DDR interface.
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        # Clock domain for peripherals (such as HDMI output).
        self.clock_domains.cd_base50 = ClockDomain()
        self.clock_domains.cd_encoder = ClockDomain()

        self.reset = Signal()

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

        # Unbuffered output signals from the PLL. They need to be buffered
        # before feeding into the fabric.
        unbuf_sdram_full = Signal()
        unbuf_sdram_half_a = Signal()
        unbuf_sdram_half_b = Signal()
        unbuf_encoder = Signal()
        unbuf_sys = Signal()
        unbuf_unused = Signal()

        # PLL signals
        pll_lckd = Signal()
        pll_fb = Signal()
        self.specials.pll = Instance(
            "PLL_ADV",
            name="crg_pll_adv",
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
            # ( 50MHz) unused? - Was peripheral
            o_CLKOUT4=unbuf_unused, p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=12,
            # ( 75MHz) sysclk
            o_CLKOUT5=unbuf_sys, p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,
        )


        # power on reset?
        reset = ~platform.request("cpu_reset") | self.reset
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)

        # System clock - 75MHz
        self.specials += Instance("BUFG", name="sys_bufg", i_I=unbuf_sys, o_O=self.cd_sys.clk)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))


        # SDRAM clocks
        # ------------------------------------------------------------------------------
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # sdram_full
        self.specials += Instance("BUFPLL", name="sdram_full_bufpll",
                                  p_DIVIDE=4,
                                  i_PLLIN=unbuf_sdram_full, i_GCLK=self.cd_sys.clk,
                                  i_LOCKED=pll_lckd,
                                  o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk4x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]
        # sdram_half
        self.specials += Instance("BUFG", name="sdram_half_a_bufpll", i_I=unbuf_sdram_half_a, o_O=self.cd_sdram_half.clk)
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", name="sdram_half_b_bufpll", i_I=unbuf_sdram_half_b, o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted,
                                  i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)

        # Peripheral clock - 50MHz
        # ------------------------------------------------------------------------------
        # The peripheral clock is kept separate from the system clock to allow
        # the system clock to be increased in the future.
        dcm_base50_locked = Signal()
        self.specials += [
            Instance("DCM_CLKGEN", name="crg_periph_dcm_clkgen",
                     p_CLKIN_PERIOD=10.0,
                     p_CLKFX_MULTIPLY=2,
                     p_CLKFX_DIVIDE=4,
                     p_CLKFX_MD_MAX=0.5, # CLKFX_MULTIPLY/CLKFX_DIVIDE
                     p_CLKFXDV_DIVIDE=2,
                     p_SPREAD_SPECTRUM="NONE",
                     p_STARTUP_WAIT="FALSE",

                     i_CLKIN=clk100a,
                     o_CLKFX=self.cd_base50.clk,
                     o_LOCKED=dcm_base50_locked,
                     i_FREEZEDCM=0,
                     i_RST=ResetSignal(),
                     ),
            AsyncResetSynchronizer(self.cd_base50,
                self.cd_sys.rst | ~dcm_base50_locked)
        ]
        platform.add_period_constraint(self.cd_base50.clk, 20)

        # Encoder clock - 66 MHz
        # ------------------------------------------------------------------------------
        self.specials += Instance("BUFG", name="encoder_bufg", i_I=unbuf_encoder, o_O=self.cd_encoder.clk)
        self.specials += AsyncResetSynchronizer(self.cd_encoder, self.cd_sys.rst)


class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        "spiflash",
#        "cas",
        "ddrphy",
        "info",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, **kwargs):
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size']=0x8000
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size']=0x8000

        clk_freq = 75*1000000
        SoCSDRAM.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        self.submodules.info = info.Info(platform, self.__class__.__name__)

        self.submodules.spiflash = spi_flash.SpiFlash(
            platform.request("spiflash4x"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        bios_size = 0x8000
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)

        #self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)

        # sdram
        sdram_module = P3R1GE4JGF(self.clk_freq, "1:2")
        self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
            platform.request("ddram"),
            sdram_module.memtype,
            rd_bitslip=0,
            wr_bitslip=4,
            dqs_ddr_alignment="C0")
        controller_settings = ControllerSettings(with_bandwidth=True)
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=controller_settings)
        self.comb += [
            self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
            self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
        ]


SoC = BaseSoC
