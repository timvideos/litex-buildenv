import sys
import struct
import os.path
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import Pins, Subsignal, IOStandard
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from gateware import cas
from gateware import ice40
from gateware import spi_flash

from targets.utils import csr_map_update
import platforms.ice40_up5k_b_evn as up5k


# Alternate serial port, using the second 6-pin PMOD port. Follows Digilent
# PMOD Specification Type 4, so e.g. PMOD USBUART can be used.
pmod_serial = [
    ("serial", 0,
        Subsignal("rx", Pins("PMOD:6")),
        Subsignal("tx", Pins("PMOD:5")),
        Subsignal("rts", Pins("PMOD:4")),
        Subsignal("cts", Pins("PMOD:7")),
        IOStandard("LVCMOS33"),
    ),
]

class _CRG(Module):
    def __init__(self, platform):
        clk12 = platform.request("clk12")

        self.clock_domains.cd_sys = ClockDomain()
        self.reset = Signal()

        # FIXME: Use PLL, increase system clock to 32 MHz, pending nextpnr
        # fixes.
        self.comb += self.cd_sys.clk.eq(clk12)

        # POR reset logic- POR generated from sys clk, POR logic feeds sys clk
        # reset.
        self.clock_domains.cd_por = ClockDomain()
        reset_delay = Signal(12, reset=4095)
        self.comb += [
            self.cd_por.clk.eq(self.cd_sys.clk),
            self.cd_sys.rst.eq(reset_delay != 0)
        ]
        self.sync.por += \
            If(reset_delay != 0,
                reset_delay.eq(reset_delay - 1)
            )
        self.specials += AsyncResetSynchronizer(self.cd_por, self.reset)


class BaseSoC(SoCCore):
    csr_peripherals = (
        "spiflash",
        "cas",
    )
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    mem_map = {
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, platform, **kwargs):
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size']=0
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size']=0

        # FIXME: Force either lite or minimal variants of CPUs; full is too big.
        platform.add_extension(pmod_serial)
        platform.add_extension(up5k.spiflash)
        clk_freq = int(12e6)

        kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size
        SoCCore.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        # Control and Status
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)

        # SPI flash peripheral
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
        self.add_memory_region(
            "rom", kwargs['cpu_reset_address'], bios_size,
            type="cached+linker")
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)

        # SPRAM- UP5K has single port RAM, might as well use it as SRAM to
        # free up scarce block RAM.
        self.submodules.spram = ice40.SPRAM(size=128*1024)
        self.register_mem("sram", self.mem_map["sram"], self.spram.bus, 0x20000)

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        self.add_memory_region("user_flash",
            self.flash_boot_address,
            # Leave a grace area- possible one-by-off bug in add_memory_region?
            # Possible fix: addr < origin + length - 1
            platform.spiflash_total_size - (self.flash_boot_address - self.mem_map["spiflash"]) - 0x100,
            type="cached+linker")

        # Disable final deep-sleep power down so firmware words are loaded
        # onto softcore's address bus.
        platform.toolchain.build_template[3] = "icepack -s {build_name}.txt {build_name}.bin"
        platform.toolchain.nextpnr_build_template[2] = "icepack -s {build_name}.txt {build_name}.bin"


SoC = BaseSoC
