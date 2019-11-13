# Support for simulation via verilator
from migen import *
from migen.genlib.io import CRG

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores import uart

from litedram.common import PhySettings
from litedram.modules import IS42S16160
from litedram.phy.model import SDRAMPHYModel
from litedram.core.controller import ControllerSettings

from gateware import firmware

from targets.utils import csr_map_update


class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        ,
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, **kwargs):
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size']=0x8000
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size']=0x8000
        if 'firmware_ram_size' not in kwargs:
            kwargs['firmware_ram_size']=0x10000
        if 'firmware_filename' not in kwargs:
            kwargs['firmware_filename'] = "build/sim_{}_{}/software/firmware/firmware.fbi".format(
                self.__class__.__name__.lower()[:-3], kwargs.get('cpu_type', 'lm32'))

        clk_freq = int((1/(platform.default_clk_period))*1000000000)
        SoCSDRAM.__init__(self, platform, clk_freq, with_uart=False, **kwargs)

        self.submodules.crg = CRG(platform.request(platform.default_clk_name))

        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)

        # firmware
        self.submodules.firmware_ram = firmware.FirmwareROM(firmware_ram_size, firmware_filename)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.flash_boot_address = self.mem_map["firmware_ram"]
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)

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


SoC = BaseSoC
