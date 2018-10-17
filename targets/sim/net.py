from litex.soc.integration.soc_core import mem_decoder

from liteeth.phy.model import LiteEthPHYModel
from liteeth.core.mac import LiteEthMAC

from targets.utils import csr_map_update
from targets.sim.base import BaseSoC


class NetSoC(BaseSoC):
# FIXME: The sim seems to require ethphy at 18 and ethmac at 19!?
#    csr_peripherals = (
#        "ethphy",
#        "ethmac",
#    )
#    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    csr_map = {
        "ethphy": 18,
        "ethmac": 19,
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "ethmac": 3,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, *args, **kwargs):
        # Need a larger integrated ROM on or1k to fit the BIOS with TFTP support.
        if 'integrated_rom_size' not in kwargs and kwargs.get('cpu_type', 'lm32') != 'lm32':
            kwargs['integrated_rom_size'] = 0x10000

        BaseSoC.__init__(self, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHYModel(self.platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)

        # Disable the flash boot address under the net target, so we boot from
        # net
        self.flash_boot_address = None

    def configure_iprange(self, iprange):
        iprange = [int(x) for x in iprange.split(".")]
        while len(iprange) < 4:
            iprange.append(0)
        # Our IP address
        self._configure_ip("LOCALIP", iprange[:-1]+[50])
        # IP address of tftp host
        remoteip = iprange[:-1]+[100]
        self.remoteip = ".".join(map(str, remoteip))
        self._configure_ip("REMOTEIP", remoteip)

    def _configure_ip(self, ip_type, ip):
        for i, e in enumerate(ip):
            s = ip_type + str(i + 1)
            s = s.upper()
            self.add_constant(s, e)


SoC = NetSoC
