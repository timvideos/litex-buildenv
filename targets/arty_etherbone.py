from targets.arty_base import *

from liteeth.common import *
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone

from migen.fhdl.specials import Keep


class EtherboneSoC(BaseSoC):
    csr_map = {
        "ethphy":  30,
        "ethcore": 31,
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self, platform,
                 mac_address=0x10e2d5000000,
                 ip_address="192.168.1.42",
                 **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        # Ethernet PHY and UDP/IP stack
        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"),
                                               platform.request("eth"))
        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy,
                                                   mac_address,
                                                   convert_ip(ip_address),
                                                   self.clk_freq,
                                                   with_icmp=True)

        # Etherbone bridge
        self.submodules.etherbone = LiteEthEtherbone(self.ethcore.udp, 20000)
        self.add_wb_master(self.etherbone.master.bus)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_clocks_rx}" TNM_NET = "GRPeth_clocks_rx";
NET "{eth_rx_clk}" TNM_NET = "GRPeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "GRPeth_tx_clk";
TIMESPEC "TIG1" = FROM "GRPeth_clocks_rx" TO "GRPsys_clk" TIG;
TIMESPEC "TIG2" = FROM "GRPsys_clk" TO "GRPeth_clocks_rx" TIG;
TIMESPEC "TIG3" = FROM "GRPeth_tx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TIG4" = FROM "GRPsys_clk" TO "GRPeth_tx_clk" TIG;
TIMESPEC "TIG5" = FROM "GRPeth_rx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TIG6" = FROM "GRPsys_clk" TO "GRPeth_rx_clk" TIG;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)


class LogicAnalyzerSoC(EtherboneSoC):
    csr_map = {
        "logic_analyzer": 22
    }
    csr_map.update(EtherboneSoC.csr_map)

    def __init__(self, platform, **kwargs):
        from litescope.frontend.logic_analyzer import LiteScopeLogicAnalyzer
        from litescope.core.port import LiteScopeTerm
        EtherboneSoC.__init__(self, platform, **kwargs)
        debug = (
            platform.request("logic_analyzer_ios") # TODO
        )
        self.submodules.logic_analyzer = LiteScopeLogicAnalyzer(debug, 4096)
        self.logic_analyzer.trigger.add_port(
            LiteScopeTerm(self.logic_analyzer.dw)
        )

    def do_exit(self, vns):
        self.logic_analyzer.export(vns, "software/logic_analyzer.csv")


default_subtarget = EtherboneSoC
