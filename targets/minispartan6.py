from fractions import Fraction

from migen.fhdl.std import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.actorlib.fifo import SyncFIFO

from misoclib.mem import sdram
from misoclib.mem.sdram.module import AS4C16M16
from misoclib.mem.sdram.phy import gensdrphy
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.soc.sdram import SDRAMSoC

from misoclib.com.liteusb.common import *
from misoclib.com.liteusb.phy.ft2232h import FT2232HPHYAsynchronous
from misoclib.com.liteusb.core import LiteUSBCore

class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_ftdi = ClockDomain()

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

        self.comb += [
            self.cd_ftdi.clk.eq(self.cd_sys.clk),
            self.cd_ftdi.rst.eq(self.cd_sys.rst)
        ]


class BaseSoC(SDRAMSoC):
    default_platform = "minispartan6"

    def __init__(self, platform, sdram_controller_settings=LASMIconSettings(), **kwargs):
        clk_freq = 80*1000000
        SDRAMSoC.__init__(self, platform, clk_freq,
                          integrated_rom_size=0x8000,
                          sdram_controller_settings=sdram_controller_settings,
                          **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)

        if not self.integrated_main_ram_size:
            self.submodules.sdrphy = gensdrphy.GENSDRPHY(platform.request("sdram"),
                                                         AS4C16M16(clk_freq))
            self.register_sdram_phy(self.sdrphy)


class USBSoC(BaseSoC):
    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.usb_phy = FT2232HPHYAsynchronous(platform.request("ftdi_fifo"), self.clk_freq)
        self.submodules.usb_core = LiteUSBCore(self.usb_phy)

        usb_port = self.usb_core.crossbar.get_port(0x00)

        leds = Cat(iter([platform.request("user_led", i) for i in range(8)]))

        usb_loopback_fifo = SyncFIFO(user_description(8), 1024, buffered=True)
        self.submodules += usb_loopback_fifo
        self.comb += [
            usb_port.source.connect(usb_loopback_fifo.sink),
            usb_loopback_fifo.source.connect(usb_port.sink)
        ]
        self.sync += [
            If(usb_port.source.stb & usb_port.source.ack,
                leds.eq(usb_port.source.data)
            )
        ]

default_subtarget = BaseSoC
