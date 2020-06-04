# Support for Numato Galatea - https://numato.com/product/galatea-pci-express-spartan-6-fpga-development-board

from migen import *

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT41J128M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

from gateware import cas
from gateware import info
from gateware import spi_flash

from targets.utils import dict_set_max
from .crg import _CRG


class BaseSoC(SoCSDRAM):
    mem_map = {**SoCSDRAM.mem_map, **{
        'spiflash': 0x20000000,
    }}

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x4000)

        sys_clk_freq = 50*1000000
        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # DDR3 SDRAM -------------------------------------------------------------------------------
        if True:
            sdram_module = MT41J128M16(self.clk_freq, "1:4")
            self.submodules.ddrphy = s6ddrphy.S6QuarterRateDDRPHY(
                platform.request("ddram"),
                rd_bitslip=0,
                wr_bitslip=4,
                dqs_ddr_alignment="C0")
            controller_settings = ControllerSettings(with_bandwidth=True)
            self.add_csr("ddrphy")
            self.register_sdram(
                self.ddrphy,
                geom_settings   = sdram_module.geom_settings,
                timing_settings = sdram_module.timing_settings,
                controller_settings=controller_settings)
            self.comb += [
                self.ddrphy.clk8x_wr_strb.eq(self.crg.clk8x_wr_strb),
                self.ddrphy.clk8x_rd_strb.eq(self.crg.clk8x_rd_strb),
            ]

        # Basic peripherals ------------------------------------------------------------------------
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        self.add_csr("cas")



SoC = BaseSoC
