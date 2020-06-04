from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *

from liteeth.core.mac import LiteEthMAC
from liteeth.phy.rmii import LiteEthPHYRMII

from targets.utils import dict_set_max
from targets.netv2.base import SoC as BaseSoC


class NetSoC(BaseSoC):
    mem_map = {**BaseSoC.mem_map, **{
        "ethmac": 0xb0000000,
    }}

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYRMII(
            platform.request("eth_clocks"),
            platform.request("eth"))
        self.add_csr("ethphy")
        self.submodules.ethmac = LiteEthMAC(
            phy=self.ethphy, dw=32, interface="wishbone", endianness=self.cpu.endianness)

        self.add_csr("ethmac")
        self.add_interrupt("ethmac")
        self.add_wb_slave(self.mem_map["ethmac"], self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"], 0x2000, type="io")

        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 40.0)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 40.0)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk,
            self.ethphy.crg.cd_eth_tx.clk)



SoC = NetSoC
