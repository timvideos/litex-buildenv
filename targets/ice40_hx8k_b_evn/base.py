#!/usr/bin/env python3
import sys
import struct
import os.path
import argparse

from migen import *

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from gateware import cas
from gateware import info
from gateware import spi_flash

from .crg import _CRG

from litex.soc.cores.uart import UARTWishboneBridge

class BaseSoC(SoCCore):
    mem_map = {**SoCCore.mem_map, **{
        'spiflash': 0x20000000,
        'vexriscv_debug': 0xf00f0000,
        'sram': 0,
    }}

    def __init__(self, platform, **kwargs):
        kwargs['integrated_rom_size']=None
        kwargs['integrated_sram_size']=0x2800

        kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size

        # FIXME: Force either lite or minimal variants of CPUs; full is too big.
        kwargs['uart_name'] = 'crossover'
        sys_clk_freq = int(12e6)
        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, **kwargs)

        self.submodules.uart_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200)
        self.add_wb_master(self.uart_bridge.wishbone)
        self.register_mem("vexriscv_debug", 0xf00f0000, self.cpu.debug_bus, 0x100)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # Basic peripherals ------------------------------------------------------------------------
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        self.add_csr("cas")

        # Memory mapped SPI Flash ------------------------------------------------------------------
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div,
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
        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region(
            "rom", kwargs['cpu_reset_address'], bios_size,
            type="cached+linker")
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        #self.add_memory_region("user_flash",
        #    self.flash_boot_address,
        #    # Leave a grace area- possible one-by-off bug in add_memory_region?
        #    # Possible fix: addr < origin + length - 1
        #    platform.spiflash_total_size - (self.flash_boot_address - self.mem_map["spiflash"]) - 0x100,
        #    type="cached+linker")

        # Disable final deep-sleep power down so firmware words are loaded
        # onto softcore's address bus.
        platform.toolchain.build_template[3] = "icepack -s {build_name}.txt {build_name}.bin"
        platform.toolchain.nextpnr_build_template[1] += " --placer heap"
        platform.toolchain.nextpnr_build_template[2] = "icepack -s {build_name}.txt {build_name}.bin"


SoC = BaseSoC
