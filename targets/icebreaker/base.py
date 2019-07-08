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

from gateware import up5kspram
from gateware import cas
from gateware import spi_flash

from targets.utils import csr_map_update
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


class _SBLED(Module, AutoCSR):
    def __init__(self, pads):

        rgba_pwm = Signal(3)

        self.dat = CSRStorage(8)
        self.addr = CSRStorage(4)
        self.ctrl = CSRStorage(4)

        self.specials += Instance("SB_RGBA_DRV",
            i_CURREN = self.ctrl.storage[1],
            i_RGBLEDEN = self.ctrl.storage[2],
            i_RGB0PWM = rgba_pwm[0],
            i_RGB1PWM = rgba_pwm[1],
            i_RGB2PWM = rgba_pwm[2],
            o_RGB0 = pads.rgb0,
            o_RGB1 = pads.rgb1,
            o_RGB2 = pads.rgb2,
            p_CURRENT_MODE = "0b1",
            p_RGB0_CURRENT = "0b000011",
            p_RGB1_CURRENT = "0b000001",
            p_RGB2_CURRENT = "0b000011",
        )

        self.specials += Instance("SB_LEDDA_IP",
            i_LEDDCS = self.dat.re,
            i_LEDDCLK = ClockSignal(),
            i_LEDDDAT7 = self.dat.storage[7],
            i_LEDDDAT6 = self.dat.storage[6],
            i_LEDDDAT5 = self.dat.storage[5],
            i_LEDDDAT4 = self.dat.storage[4],
            i_LEDDDAT3 = self.dat.storage[3],
            i_LEDDDAT2 = self.dat.storage[2],
            i_LEDDDAT1 = self.dat.storage[1],
            i_LEDDDAT0 = self.dat.storage[0],
            i_LEDDADDR3 = self.addr.storage[3],
            i_LEDDADDR2 = self.addr.storage[2],
            i_LEDDADDR1 = self.addr.storage[1],
            i_LEDDADDR0 = self.addr.storage[0],
            i_LEDDDEN = self.dat.re,
            i_LEDDEXE = self.ctrl.storage[0],
            # o_LEDDON = led_is_on, # Indicates whether LED is on or not
            # i_LEDDRST = ResetSignal(), # This port doesn't actually exist
            o_PWMOUT0 = rgba_pwm[0], 
            o_PWMOUT1 = rgba_pwm[1], 
            o_PWMOUT2 = rgba_pwm[2],
            o_LEDDON = Signal(), 
        )

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

        # Assume user still has LEDs/Buttons still attached to the PCB or as
        # a PMOD; pinout is identical either way.
        platform.add_extension(icebreaker.break_off_pmod)
        clk_freq = int(12e6)

        kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size
        SoCCore.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/clk_freq)

        # Control and Status
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)

        # SPI flash peripheral
        # TODO: Inferred tristate not currently supported by nextpnr; upgrade
        # to spiflash4x when possible.
        self.submodules.spiflash = spi_flash.SpiFlashSingle(
            platform.request("spiflash"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div,
            endianness=self.cpu.endianness)
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        # rgb led connector
        platform.add_extension(icebreaker.rgb_led)
        self.submodules.rgbled = _SBLED(platform.request("rgbled", 0))
        self.add_csr("rgbled")

        bios_size = 0x8000
        self.add_constant("ROM_DISABLE", 1)
        self.add_memory_region("rom", kwargs['cpu_reset_address'], bios_size)
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size

        # SPRAM- UP5K has single port RAM, might as well use it as SRAM to
        # free up scarce block RAM.
        self.submodules.spram = up5kspram.Up5kSPRAM(size=128*1024)
        self.register_mem("sram", 0x10000000, self.spram.bus, 0x20000)

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        self.add_memory_region("user_flash",
            self.flash_boot_address,
            # Leave a grace area- possible one-by-off bug in add_memory_region?
            # Possible fix: addr < origin + length - 1
            platform.spiflash_total_size - (self.flash_boot_address - self.mem_map["spiflash"]) - 0x100)

        # Disable final deep-sleep power down so firmware words are loaded
        # onto softcore's address bus.
        platform.toolchain.build_template[3] = "icepack -s {build_name}.txt {build_name}.bin"
        platform.toolchain.nextpnr_build_template[2] = "icepack -s {build_name}.txt {build_name}.bin"

SoC = BaseSoC
