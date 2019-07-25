from litex.soc.integration.soc_core import mem_decoder

from liteeth.core.mac import LiteEthMAC
from liteeth.phy import LiteEthPHY

from targets.utils import csr_map_update
from targets.atlys.base import SoC as BaseSoC


class NetSoC(BaseSoC):
    csr_peripherals = (
        "ethphy",
        "ethmac",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, *args, **kwargs):
        # Need a larger integrated ROM on or1k to fit the BIOS with TFTP support.
        if 'integrated_rom_size' not in kwargs and kwargs.get('cpu_type', 'lm32') != 'lm32':
            kwargs['integrated_rom_size'] = 0x10000

        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHY(
            platform.request("eth_clocks"),
            platform.request("eth"),
            self.clk_freq)

        self.submodules.ethmac = LiteEthMAC(
            phy=self.ethphy, dw=32, interface="wishbone", endianness=self.cpu.endianness)
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac",
            self.mem_map["ethmac"] | self.shadow_base, 0x2000)

        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        # FIXME: This is probably too tight?
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 8.0)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk)

        self.platform.add_platform_command("""
# FIXME: ERROR:Place:1108 - A clock IOB / BUFGMUX clock component pair have
# been found that are not placed at an optimal clock IOB / BUFGMUX site pair.
# The clock IOB component <eth_clocks_rx> is placed at site <K15>.
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
# The IOB component <eth_clocks_tx> is placed at site <K16>.
NET "{eth_clocks_tx}" CLOCK_DEDICATED_ROUTE = FALSE;
""",
            eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
            eth_clocks_tx=platform.lookup_request("eth_clocks").tx,
            )

        self.add_interrupt("ethmac")

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
