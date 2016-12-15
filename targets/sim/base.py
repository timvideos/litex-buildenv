#!/usr/bin/env python3

import argparse
import importlib
import os

from litex.gen import *
from litex.gen.genlib.io import CRG

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores import uart
from litex.soc.integration.soc_core import mem_decoder

from litedram.common import PhySettings
from litedram.modules import IS42S16160
from litedram.phy.model import SDRAMPHYModel
from litedram.core.controller import ControllerSettings

from liteeth.phy.model import LiteEthPHYModel
from liteeth.core.mac import LiteEthMAC

from litevideo.output.common import *
from litevideo.output.core import VideoOutCore

from litex.boards.platforms import sim

from gateware import firmware


def csr_map_update(csr_map, csr_peripherals):
  csr_map.update(dict((n, v) for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


class VGAModel(Module):
    def __init__(self, pads):
        self.sink = sink = stream.Endpoint(video_out_layout(24))
        self.comb += [
            sink.ready.eq(1),
            pads.de.eq(sink.de),
            pads.hsync.eq(sink.hsync),
            pads.vsync.eq(sink.vsync),
            pads.r.eq(sink.data[0:8]),
            pads.g.eq(sink.data[8:16]),
            pads.b.eq(sink.data[16:24]),
        ]


class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        "video_out",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self,
                 firmware_ram_size=0x10000,
                 firmware_filename="firmware/firmware.bin",
                 **kwargs):
        platform = sim.Platform()
        SoCSDRAM.__init__(self, platform,
            clk_freq=int((1/(platform.default_clk_period))*1000000000),
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            with_uart=False,
            **kwargs)
        self.submodules.crg = CRG(platform.request(platform.default_clk_name))

        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)

        # firmware
        self.submodules.firmware_ram = firmware.FirmwareROM(firmware_ram_size, firmware_filename)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["firmware_ram"])

        # sdram
        sdram_module = IS42S16160(self.clk_freq, "1:1")
        phy_settings = PhySettings(
            memtype="SDR",
            dfi_databits=1*32,
            nphases=1,
            rdphase=0,
            wrphase=0,
            rdcmdphase=0,
            wrcmdphase=0,
            cl=2,
            read_latency=4,
            write_latency=0
        )
        self.submodules.sdrphy = SDRAMPHYModel(sdram_module, phy_settings)
        controller_settings = ControllerSettings(with_refresh=False)
        self.register_sdram(self.sdrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=controller_settings)
        # reduce memtest size to speed up simulation
        self.add_constant("MEMTEST_DATA_SIZE", 1024)
        self.add_constant("MEMTEST_ADDR_SIZE", 1024)
        self.add_constant("SIMULATION", 1)

        self.submodules.video_out = VideoOutCore(self.sdram.crossbar.get_port())
        self.submodules.vga = VGAModel(platform.request("vga"))
        self.comb += self.video_out.source.connect(self.vga.sink)


class MiniSoC(BaseSoC):
    csr_map = {
        "ethphy": 18,
        "ethmac": 19,
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "ethmac": 2,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, *args, **kwargs):
        BaseSoC.__init__(self, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYModel(self.platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)
