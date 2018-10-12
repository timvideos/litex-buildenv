from litex.soc.cores import uart
from litex.soc.cores.uart import UARTWishboneBridge

from litescope import LiteScopeAnalyzer
from litescope import LiteScopeIO

from targets.utils import csr_map_update
from targets.ice40_up5k_b_evn.base import BaseSoC


class BridgeSoC(BaseSoC):
    csr_peripherals = (
        "analyzer",
        "io",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        kwargs['cpu_type'] = None
        BaseSoC.__init__(self, platform, *args, with_uart=False, **kwargs)

        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), self.clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)


SoC = BridgeSoC
