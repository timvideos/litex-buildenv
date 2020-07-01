from litex.soc.integration.soc_sdram import *

from liteeth.mac import LiteEthMAC
from liteeth.phy import LiteEthPHY

from targets.utils import dict_set_max
from .base import BaseSoC


class NetSoC(BaseSoC):
    mem_map = {**BaseSoC.mem_map, **{
        "ethmac": 0xb0000000,
    }}

    def __init__(self, platform, *args, **kwargs):
        # Need a larger integrated ROM to fit the BIOS with TFTP support.
        dict_set_max(kwargs, 'integrated_rom_size', 0x10000)

        BaseSoC.__init__(self, platform, *args, **kwargs)

        # Ethernet ---------------------------------------------------------------------------------
        # Ethernet PHY
        self.submodules.ethphy = LiteEthPHY(
            platform.request("eth_clocks"),
            platform.request("eth"))
        self.add_csr("ethphy")

        # Ethernet MAC
        ethmac_win_size = 0x2000
        self.submodules.ethmac = LiteEthMAC(
            phy        = self.ethphy,
            dw         = 32,
            interface  = "wishbone",
            endianness = self.cpu.endianness)
        self.add_wb_slave(self.mem_map["ethmac"], self.ethmac.bus, ethmac_win_size)
        self.add_memory_region("ethmac", self.mem_map["ethmac"], ethmac_win_size, type="io")
        self.add_csr("ethmac")
        self.add_interrupt("ethmac")
        # timing constraints
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 1e9/25e6)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 1e9/25e6)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk,
            self.ethphy.crg.cd_eth_tx.clk)

    def configure_iprange(self, iprange):
        iprange = [int(x) for x in iprange.split(".")]
        while len(iprange) < 4:
            iprange.append(0)
        # Our IP address
        self._configure_ip("LOCALIP", iprange[:-1]+[50])
        # IP address of tftp host
        self._configure_ip("REMOTEIP", iprange[:-1]+[100])

    def _configure_ip(self, ip_type, ip):
        for i, e in enumerate(ip):
            s = ip_type + str(i + 1)
            s = s.upper()
            self.add_constant(s, e)


SoC = NetSoC
