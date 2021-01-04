import sys
import struct
import os.path
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import Pins, Subsignal, IOStandard
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage

from gateware import ice40
from gateware import cas
from gateware import spi_flash

from targets.utils import define_flash_constants
from platforms import icebreaker


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
        reset = self.reset | ~platform.request("user_btn_n")
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
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)


class BaseSoC(SoCCore):
    mem_map = {**SoCCore.mem_map, **{
        "spiflash": 0xa0000000,
    }}

    def __init__(self, platform, **kwargs):
        # disable SRAM, it'll be added later
        kwargs['integrated_sram_size'] = 0x0

        # disable ROM, it'll be added later
        kwargs['integrated_rom_size'] = 0x0

        # FIXME: Force either lite or minimal variants of CPUs; full is too big.

        # Assume user still has LEDs/Buttons still attached to the PCB or as
        # a PMOD; pinout is identical either way.
        clk_freq = int(12e6)

        kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size
        SoCCore.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        # Control and Status
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)
        self.add_csr("cas")

        # SPI flash peripheral
        # TODO: Inferred tristate not currently supported by nextpnr; upgrade
        # to spiflash4x when possible.
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div,
            endianness=self.cpu.endianness)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        # rgb led connector
        platform.add_extension(icebreaker.rgb_led)
        self.submodules.rgbled = ice40.LED(platform.request("rgbled", 0))
        self.add_csr("rgbled")

        bios_size = 0x8000
        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region(
            "rom", kwargs['cpu_reset_address'], bios_size,
            type="cached+linker")
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        define_flash_constants(self)

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


SoC = BaseSoC
