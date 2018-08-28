# Support for the TinyFPGA B2 board

import sys
import struct
from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.build.lattice.programmer import TinyFpgaBProgrammer

from migen import *
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer

from targets.utils import csr_map_update


class _CRG(Module):
    def __init__(self, platform):
        clk16 = platform.request("clk16")
        rst = platform.request("rst")
        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys = ClockDomain()
        reset_delay = Signal(12, reset=4095)
        self.comb += [
            self.cd_por.clk.eq(clk16),
            self.cd_sys.clk.eq(clk16),
            self.cd_sys.rst.eq(reset_delay != 0)
        ]
        self.sync.por += \
            If(rst,
                reset_delay.eq(0)
            ).Elif(reset_delay != 0,
                reset_delay.eq(reset_delay - 1)
            )


class BaseSoC(SoCCore):
    csr_peripherals = (
        "spiflash",
        "info",
        "cas",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, **kwargs):
        clk_freq = int(16e6)

        integrated_rom_size = 0
        integrated_rom_init = []
        if with_cpu:
            integrated_rom_size = 0x2000
            integrated_rom_init = get_firmware_data("./firmware/firmware.bin", 0x2000)

        SoCCore.__init__(self, platform, clk_freq,
            cpu_type="lm32" if with_cpu else None, cpu_variant="minimal",
            csr_data_width=8,
            with_uart=with_cpu, uart_baudrate=9600,
            with_timer=with_cpu,
            ident="TinyFPGA Test SoC",
            ident_version=True,
            integrated_rom_size=integrated_rom_size,
            integrated_rom_init=integrated_rom_init)

        self.submodules.crg = _CRG(platform)

        # bridge
        if not with_cpu:
            self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=9600))
            self.add_wb_master(self.cpu_or_bridge.wishbone)

        led_counter = Signal(32)
        self.sync += led_counter.eq(led_counter + 1)
        self.comb += [
            platform.request("user_led", 0).eq(led_counter[22]),
            platform.request("user_led", 1).eq(led_counter[23]),
            platform.request("user_led", 2).eq(led_counter[24])
        ]

SoC = BaseSoC
