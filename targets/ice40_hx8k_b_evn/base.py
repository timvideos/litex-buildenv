#!/usr/bin/env python3
import sys
import struct
import os.path
import argparse

from migen import *

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.cpu.vexriscv.core import VexRiscv

from gateware import cas
from gateware import info
from gateware import spi_flash

from targets.utils import dict_set_max, platform_toolchain_extend, round_up_to_4

from .crg import _CRG

from litex.soc.cores.uart import UARTWishboneBridge


class BaseSoC(SoCCore):
    mem_map = {**SoCCore.mem_map, **{
        'spiflash': 0x20000000,
        'vexriscv_debug': 0xf00f0000,
        'sram': 0,
    }}
    del mem_map['rom']

    def __init__(self, platform, **kwargs):
        bios_size = 0x8000
        spiflash_base = self.mem_map['spiflash']
        spiflash_bios_base = spiflash_base + platform.gateware_size
        # Leave a grace area- possible one-by-off bug in add_memory_region?
        # Possible fix: addr < origin + length - 1
        spiflash_user_base = spiflash_base + platform.gateware_size + bios_size
        spiflash_user_size = platform.spiflash_total_size - round_up_to_4(platform.gateware_size + bios_size)
        print("""
  Flash start: {:08x}
Gateware size: {:08x}

   BIOS start: {:08x}
   BIOS  size: {:08x}
   BIOS   end: {:08x}

   User start: {:08x}
   User  size: {:08x}
   User   end: {:08x}

  Flash   end: {:08x}
""".format(
    spiflash_base,
    platform.gateware_size,

    spiflash_bios_base,
    bios_size,
    spiflash_bios_base+bios_size,

    spiflash_user_base,
    spiflash_user_size,
    spiflash_user_base+spiflash_user_size,

    spiflash_base + platform.spiflash_total_size,
))

        kwargs['cpu_reset_address'] = spiflash_bios_base

        dict_set_max(kwargs, 'integrated_sram_size', 0x2800)

        # disable ROM, it'll be added later
        kwargs['integrated_rom_size'] = 0x0


        kwargs['uart_name'] = 'crossover'

        sys_clk_freq = int(12e6)
        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, **kwargs)

        #if isinstance(self.cpu, VexRiscv):
        #    self.cpu.use_external_variant("gateware/cpu/VexRiscv_Fomu_Debug.v")

        self.submodules.uart_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200)
        self.add_wb_master(self.uart_bridge.wishbone)

        if isinstance(self.cpu, VexRiscv) and "debug" in self.cpu.variant:
            self.register_mem(
                name="vexriscv_debug",
                address=0xf00f0000,
                interface=self.cpu.debug_bus,
                size=0x100)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # Basic peripherals ------------------------------------------------------------------------
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        #self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        #self.add_csr("cas")

        # Memory mapped SPI Flash ------------------------------------------------------------------
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div,
            endianness='little') #self.cpu.endianness)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.add_constant("SPIFLASH_TOTAL_SIZE", platform.spiflash_total_size)
        self.register_mem(
            name="spiflash",
            address=spiflash_base,
            interface=self.spiflash.bus,
            size=platform.spiflash_total_size)

        # BIOS is running from flash
        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region(
            name="rom",
            origin=spiflash_bios_base,
            length=bios_size,
            type="cached+linker")

        self.flash_boot_address = spiflash_user_base
        self.add_constant("FLASH_BOOT_ADDRESS", spiflash_user_base)

        # Make the LEDs flash ----------------------------------------------------------------------
        cnt = Signal(32)
        self.sync += [
            cnt.eq(cnt + 1),
        ]
        self.comb += [
            self.platform.request("user_led").eq(cnt[31]),
            self.platform.request("user_led").eq(cnt[30]),
            self.platform.request("user_led").eq(cnt[29]),
            self.platform.request("user_led").eq(cnt[28]),
            self.platform.request("user_led").eq(cnt[27]),
            self.platform.request("user_led").eq(cnt[26]),
            self.platform.request("user_led").eq(cnt[25]),
        ]

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        self.add_memory_region(
            name="user_flash",
            origin=spiflash_user_base,
            length=spiflash_user_size,
            type="cached+linker")

        platform_toolchain_extend(platform, "nextpnr-ice40", "--placer heap")


SoC = BaseSoC
