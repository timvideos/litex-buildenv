# Support for Digilent Nexys Video board
from migen import *

from litex.soc.cores.uart import * #UART, RS232PHYInterface, RS232PHY, RS232PHYMultiplexer, Stream2Wishbone
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT41K256M16
from litedram.phy import s7ddrphy
from litedram.core import ControllerSettings

# from gateware import cas
from gateware import info
from gateware import oled
from gateware import spi_flash

from targets.utils import dict_set_max
from .crg import _CRG


class BaseSoC(SoCSDRAM):
    mem_map = {**SoCSDRAM.mem_map, **{
        'spiflash': 0x20000000,
    }}

    #    "oled",
    #    "uart",
    #    "uart_phy",

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x8000)

        sys_clk_freq = int(100e6)

        # disable uart
        kwargs['with_uart'] = False

        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # DDR3 SDRAM -------------------------------------------------------------------------------
        if True:
            sdram_module = MT41K256M16(sys_clk_freq, "1:4")
            self.submodules.ddrphy = s7ddrphy.A7DDRPHY(
                platform.request("ddram"),
                memtype      = sdram_module.memtype,
                nphases      = 4,
                sys_clk_freq = sys_clk_freq)
            self.add_csr("ddrphy")
            self.add_constant("READ_LEVELING_BITSLIP", 3)
            self.add_constant("READ_LEVELING_DELAY", 14)
            self.register_sdram(
                self.ddrphy,
                geom_settings   = sdram_module.geom_settings,
                timing_settings = sdram_module.timing_settings,
                controller_settings=ControllerSettings(
                    with_bandwidth=True,
                    cmd_buffer_depth=8,
                    with_refresh=True))

        # Extended UART ----------------------------------------------------------------------------
        uart_interfaces = [RS232PHYInterface() for i in range(2)]
        self.submodules.uart = UART(uart_interfaces[0])
        self.submodules.bridge = Stream2Wishbone(uart_interfaces[1], sys_clk_freq)
        self.add_wb_master(self.bridge.wishbone)
        self.add_csr("uart")
        self.add_interrupt("uart")

        self.submodules.uart_phy = RS232PHY(platform.request("serial"), self.clk_freq, 115200)
        self.submodules.uart_multiplexer = RS232PHYMultiplexer(uart_interfaces, self.uart_phy)
        self.comb += self.uart_multiplexer.sel.eq(platform.request("user_sw", 0))
        self.add_csr("uart_phy")

        # Basic peripherals ------------------------------------------------------------------------
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        # self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        # self.add_csr("cas")
        self.submodules.oled = oled.OLED(platform.request("oled"))
        self.add_csr("oled")

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
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)


SoC = BaseSoC
