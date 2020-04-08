import sys
import struct
import os.path
import argparse

from migen import *

from litex.build.generic_platform import Pins, Subsignal, IOStandard
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from gateware import cas
from gateware import spi_flash

from targets.utils import dict_set_max, define_flash_constants
from .crg import _CRG


serial =  [
    ("serial", 0,
        Subsignal("rx", Pins("GPIO:0")), # Pin 1 - A2 - Silkscreen 1
        Subsignal("tx", Pins("GPIO:1")), # Pin 2 - A1 - Silkscreen 2
        IOStandard("LVCMOS33")
    )
]


class BaseSoC(SoCCore):
    mem_map = {**SoCCore.mem_map, **{
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }}

    def __init__(self, platform, **kwargs):
        dict_set_max(kwargs, 'integrated_sram_size', 0x2800)

        # We save the ROM size passed in as the BIOS size, and then force the
        # integrated ROM size to 0 to avoid integrated ROM. 
        bios_size = kwargs['integrated_rom_size']
        kwargs['integrated_rom_size'] = 0x0

        # FIXME: Force either lite or minimal variants of CPUs; full is too big.

        platform.add_extension(serial)
        clk_freq = int(16e6)

        # Extra 0x28000 is due to bootloader bitstream.
        kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size+platform.bootloader_size
        SoCCore.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        # Control and Status
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)
        self.add_csr("cas")

        # SPI flash peripheral
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region(
            "rom", kwargs['cpu_reset_address'], bios_size,
            type="cached+linker")
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size+platform.bootloader_size
        define_flash_constants(self)

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        self.add_memory_region("user_flash",
            self.flash_boot_address,
            # Leave a grace area- possible one-by-off bug in add_memory_region?
            # Possible fix: addr < origin + length - 1
            platform.spiflash_total_size - (self.flash_boot_address - self.mem_map["spiflash"]) - 0x100,
            type="cached+linker")

        # Disable USB activity until we switch to a USB UART.
        self.comb += [platform.request("usb").pullup.eq(0)]


SoC = BaseSoC
