# Support for the MiniSpartan6+ - https://www.scarabhardware.com/minispartan6/
from fractions import Fraction

from migen.fhdl.std import *
from migen.fhdl.specials import Keep
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.actorlib.fifo import SyncFIFO

from misoclib.com.gpio import GPIOOut
from misoclib.mem.flash import spiflash
from misoclib.mem.sdram.module import AS4C16M16
from misoclib.mem.sdram.phy import gensdrphy
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.soc.sdram import SDRAMSoC

from liteusb.common import *
from liteusb.phy.ft245 import FT245PHY
from liteusb.core import LiteUSBCore
from liteusb.frontend.uart import LiteUSBUART
from liteusb.frontend.wishbone import LiteUSBWishboneBridge

from gateware import dna
from gateware import firmware
from gateware import git_info
from gateware import platform_info

from targets.common import *


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_base50 = ClockDomain()

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

        self.specials += Instance("BUFG", i_I=platform.request("clk50"), o_O=self.cd_base50.clk)


# Patch the CPU interface to map firmware_ram into main_ram region.
from misoclib.soc import cpuif
original_get_linker_regions = cpuif.get_linker_regions
def replacement_get_linker_regions(regions):
    s = original_get_linker_regions(regions)
    s += """\
REGION_ALIAS("firmware_ram", main_ram);
"""
    return s
cpuif.get_linker_regions = replacement_get_linker_regions


class BaseSoC(SDRAMSoC):
    default_platform = "minispartan6"

    csr_peripherals = (
        "spiflash",
        "ddrphy",
        "dna",
        "git_info",
        "platform_info",
    )
    csr_map_update(SDRAMSoC.csr_map, csr_peripherals)

    mem_map = {
#        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
        "spiflash": 0x30000000,  # (default shadow @0xb0000000)
    }
    mem_map.update(SDRAMSoC.mem_map)

    def __init__(self, platform,
                 firmware_ram_size=0xa000,
                 firmware_filename=None,
                 **kwargs):
        clk_freq = 80*1000000
        SDRAMSoC.__init__(self, platform, clk_freq,
                          integrated_rom_size=0x8000,
                          sdram_controller_settings=LASMIconSettings(l2_size=32, with_bandwidth=True),
                          **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)
        self.submodules.dna = dna.DNA()
        self.submodules.git_info = git_info.GitInfo()
        self.submodules.platform_info = platform_info.PlatformInfo("minispartan6"[:8], self.__class__.__name__[:8])

        if not self.integrated_main_ram_size:
            self.submodules.ddrphy = gensdrphy.GENSDRPHY(platform.request("sdram"),
                                                         AS4C16M16(clk_freq))
            self.register_sdram_phy(self.ddrphy)

        self.submodules.spiflash = spiflash.SpiFlash(
            platform.request("spiflash2x"), dummy=platform.spiflash_read_dummy_bits, div=platform.spiflash_clock_div)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size
        self.register_mem("spiflash", self.mem_map["spiflash"], self.spiflash.bus, size=platform.gateware_size)


class USBSoC(BaseSoC):
    csr_map = {
        "usb_dma": 16,
    }
    csr_map.update(BaseSoC.csr_map)

    usb_map = {
        "uart":   0,
        "dma":    1,
        "bridge": 2
    }

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, with_uart=False, **kwargs)

        self.submodules.usb_phy = FT245PHY(platform.request("usb_fifo"), self.clk_freq)
        self.submodules.usb_core = LiteUSBCore(self.usb_phy, self.clk_freq, with_crc=False)

        # UART
        usb_uart_port = self.usb_core.crossbar.get_port(self.usb_map["uart"])
        self.submodules.uart = LiteUSBUART(usb_uart_port)

        # DMA
        usb_dma_port = self.usb_core.crossbar.get_port(self.usb_map["dma"])
        usb_dma_loopback_fifo = SyncFIFO(user_description(8), 1024, buffered=True)
        self.submodules += usb_dma_loopback_fifo
        self.comb += [
            usb_dma_port.source.connect(usb_dma_loopback_fifo.sink),
            usb_dma_loopback_fifo.source.connect(usb_dma_port.sink)
        ]

        # Wishbone Bridge
        usb_bridge_port = self.usb_core.crossbar.get_port(self.usb_map["bridge"])
        usb_bridge = LiteUSBWishboneBridge(usb_bridge_port, self.clk_freq)
        self.submodules += usb_bridge
        self.add_wb_master(usb_bridge.wishbone)

        # Leds
        leds = Cat(iter([platform.request("user_led", i) for i in range(8)]))
        self.submodules.leds = GPIOOut(leds)

default_subtarget = BaseSoC
