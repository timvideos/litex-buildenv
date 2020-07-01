# Support for the MATRIX Voice
# https://www.matrix.one/products/voice
# Author: Andres Calderon <andres.calderon@admobilize.com>
# FPGA: Spartan 6 xc6slx9-2-ftg256
# Copyright 2020 MATRIX Labs
# License: BSD

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT47H32M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

from gateware import cas
from gateware import info
from gateware import spi_flash

from targets.utils import dict_set_max

from .crg import _CRG


class BaseSoC(SoCSDRAM):
    mem_map = {**SoCSDRAM.mem_map, **{
        "spiflash": 0xa0000000
    }}

    def __init__(self, platform, **kwargs):
        if kwargs.get('cpu_type', None) == 'mor1kx':
            dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        else:
            dict_set_max(kwargs, 'integrated_rom_size', 0x8000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x4000)

        kwargs['uart_baudrate']=230400

        sys_clk_freq = int(75*1000*1000)
        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

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
            div=platform.spiflash_clock_div)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.register_mem("spiflash", self.mem_map["spiflash"],
            self.spiflash.bus, size=platform.spiflash_total_size)

        bios_size = 0x8000
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)

        # SDRAM ------------------------------------------------------------------------------------
        sdram_module = MT47H32M16(self.sys_clk_freq, "1:2")
        self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
            platform.request("ddram"),
            sdram_module.memtype,
            rd_bitslip=0,
            wr_bitslip=4,
            dqs_ddr_alignment="C0")
        controller_settings = ControllerSettings(with_bandwidth=True)
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            controller_settings=controller_settings)
        self.comb += [
            self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
            self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
        ]

SoC = BaseSoC
