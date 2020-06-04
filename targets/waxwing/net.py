# Support for the Numato Saturn (http://numato.com/product/saturn-spartan-6-fpga-development-board-with-ddr-sdram)
# Original code from : https://github.com/timvideos/litex-buildenv/blob/master/targets/waxwing/base.py
# By Rohit Singh

from fractions import Fraction

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import *

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT46H32M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

from targets.utils import csr_map_update, dict_set_max
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.mac import LiteEthMAC

from litex.soc.interconnect import wishbone

from .crg import _CRG


# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
    def __init__(self, platform, **kwargs):
        dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x8000)

        clk_freq = (31 + Fraction(1, 4))*1000*1000
        SoCSDRAM.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)

        # sdram
        if not self.integrated_main_ram_size:
            sdram_module = MT46H32M16(clk_freq, "1:2")
            self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(
                platform.request("ddram"),
                sdram_module.memtype,
                rd_bitslip=2,
                wr_bitslip=3,
                dqs_ddr_alignment="C1"
            )
            self.add_csr("ddrphy")

            self.register_sdram(self.ddrphy,
                sdram_module.geom_settings,
                sdram_module.timing_settings,
                controller_settings=ControllerSettings(
                    with_bandwidth=True)
            )

            self.comb += [
                self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
                self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
            ]

# EthernetSoC --------------------------------------------------------------------------------------

class EthernetSoC(BaseSoC):
    mem_map = {
        "ethmac": 0xb0000000,
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, *args, **kwargs):
        # Need a larger integrated ROM on or1k to fit the BIOS with TFTP support.
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size'] = 0x10000
        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYMII(self.platform.request("eth_clocks"),
                                               self.platform.request("eth"))
        self.add_csr("ethphy")
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
            interface="wishbone", endianness=self.cpu.endianness)
        self.add_wb_slave(self.mem_map["ethmac"], self.ethmac.bus, 0x2000)
        self.add_memory_region("ethmac", self.mem_map["ethmac"], 0x2000, type="io")
        self.add_csr("ethmac")
        self.add_interrupt("ethmac")
        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        #self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 1e9/12.5e6)
        #self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 1e9/12.5e6)
        #self.platform.add_false_path_constraints(
        #    self.crg.cd_sys.clk,
        #    self.ethphy.crg.cd_eth_rx.clk,
        #    self.ethphy.crg.cd_eth_tx.clk)

SoC = EthernetSoC
