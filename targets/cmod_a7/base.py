# Support for the Digilent Cmod A7 Board
from migen import *

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from gateware import cas
from gateware import info
from gateware import spi_flash

from targets.utils import period_ns, dict_set_max

from .crg import _CRG


class BaseSoC(SoCCore):
    mem_map = {**SoCCore.mem_map, **{
        'spiflash': 0x20000000,
    }}

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x8000)

        sys_clk_freq = int(100e6)
        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, period_ns(sys_clk_freq))

        # Basic peripherals ------------------------------------------------------------------------
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        self.add_csr("cas")

        # Add debug interface if the CPU has one ---------------------------------------------------
        if hasattr(self.cpu, "debug_bus"):
            self.register_mem(
                name="vexriscv_debug",
                address=0xf00f0000,
                interface=self.cpu.debug_bus,
                size=0x100)

        # Memory mapped SPI Flash ------------------------------------------------------------------
        spiflash_pads = platform.request(spiflash)
        spiflash_pads.clk = Signal()
        self.specials += Instance(
            "STARTUPE2",
            i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0, i_PACK=0,
            i_USRCCLKO=spiflash_pads.clk, i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
        spiflash_dummy = {
            "spiflash_1x": 9,
            "spiflash_4x": 11,
        }
        self.submodules.spiflash = spi_flash.SpiFlash(
            spiflash_pads,
            dummy=spiflash_dummy[spiflash],
            div=2,
            endianness=self.cpu.endianness)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.add_constant("SPIFLASH_TOTAL_SIZE", platform.spiflash_total_size)
        self.add_wb_slave(
            self.mem_map["spiflash"],
            self.spiflash.bus,
            platform.spiflash_total_size)
        self.add_memory_region(
            "spiflash",
            self.mem_map["spiflash"],
            platform.spiflash_total_size)

        bios_size = 0x8000
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)


SoC = BaseSoC
