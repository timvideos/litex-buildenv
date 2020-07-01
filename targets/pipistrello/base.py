# Support for the Pipistrello - http://pipistrello.saanlima.com/

from fractions import Fraction

from migen import *

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import wishbone

from litedram.modules import MT46H32M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

#from gateware import i2c_hack
from gateware import info
from gateware import spi_flash

from targets.utils import dict_set_max, define_flash_constants
from .crg import _CRG


class BaseSoC(SoCSDRAM):
    mem_map = {**SoCSDRAM.mem_map, **{
        'spiflash': 0x20000000,
    }}

    def __init__(self, platform, **kwargs):
        if kwargs.get('cpu_type', None) == "mor1kx":
            dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        else:
            dict_set_max(kwargs, 'integrated_rom_size', 0x8000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x4000)

        sys_clk_freq = (83 + Fraction(1, 3))*1000*1000
        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # DDR2 SDRAM -------------------------------------------------------------------------------
        if True:
            sdram_module = MT46H32M16(sys_clk_freq, "1:2")
            self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
                platform.request("ddram"),
                memtype      = sdram_module.memtype,
                rd_bitslip   = 1,
                wr_bitslip   = 3,
                dqs_ddr_alignment="C1")
            self.add_csr("ddrphy")
            controller_settings = ControllerSettings(
                with_bandwidth=True)
            self.register_sdram(
                self.ddrphy,
                geom_settings   = sdram_module.geom_settings,
                timing_settings = sdram_module.timing_settings,
                controller_settings=controller_settings)
            self.comb += [
                self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
                self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
            ]

        # Basic peripherals ------------------------------------------------------------------------
        # info module
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        # control and status module
        #self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        self.add_csr("cas")

        # Add debug interface if the CPU has one ---------------------------------------------------
        if hasattr(self.cpu, "debug_bus"):
            self.register_mem(
                name="vexriscv_debug",
                address=0xf00f0000,
                interface=self.cpu.debug_bus,
                size=0x100)

        # Memory mapped SPI Flash ------------------------------------------------------------------
        self.submodules.spiflash = spi_flash.SpiFlash(
            platform.request("spiflash4x"),
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
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        define_flash_constants(self)


SoC = BaseSoC
