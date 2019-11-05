# Support for the Digilent Cmod A7 Board
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from gateware import info
from gateware import led
from gateware import spi_flash

from targets.utils import csr_map_update, period_ns


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk200 = ClockDomain()
        clk12 = platform.request("clk12")
        rst = platform.request("user_btn", 0)
        self.specials += [
            Instance("BUFG", i_I=clk12, o_O=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys, rst),
        ]


class BaseSoC(SoCCore):
    csr_peripherals = (
        "spiflash",
        "info",
    )
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    mem_map = {
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size']=0x8000
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size']=0x8000

        clk_freq = int(100e6)
        SoCCore.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, period_ns(clk_freq))

        # Basic peripherals
        self.submodules.info = info.Info(platform, self.__class__.__name__)

        # spi flash
        spiflash_pads = platform.request(spiflash)
        spiflash_pads.clk = Signal()
        self.specials += Instance("STARTUPE2",
                                  i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0, i_PACK=0,
                                  i_USRCCLKO=spiflash_pads.clk, i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
        spiflash_dummy = {
            "spiflash_1x": 9,
            "spiflash_4x": 11,
        }
        self.submodules.spiflash = spi_flash.SpiFlash(
                spiflash_pads,
                dummy=spiflash_dummy[spiflash],
                div=2)
        self.add_constant("SPIFLASH_PAGE_SIZE", 256)
        self.add_constant("SPIFLASH_SECTOR_SIZE", 0x10000)
        self.add_wb_slave(mem_decoder(self.mem_map["spiflash"]), self.spiflash.bus)
        self.add_memory_region(
            "spiflash", self.mem_map["spiflash"], 16*1024*1024)


SoC = BaseSoC
