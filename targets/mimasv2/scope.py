from litex.soc.cores import uart
from litex.soc.cores.uart import UARTWishboneBridge

from litedram.frontend.bist import LiteDRAMBISTGenerator, LiteDRAMBISTChecker

from litescope import LiteScopeAnalyzer
from litescope import LiteScopeIO

from gateware.memtest import LiteDRAMBISTCheckerScope

from targets.utils import csr_map_update
from targets.mimasv2.base import BaseSoC


class MemTestSoC(BaseSoC):
    csr_peripherals = (
        "analyzer",
        "io",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        kwargs['cpu_type'] = None
        BaseSoC.__init__(self, platform, *args, with_uart=False, **kwargs)

        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), self.clk_freq, baudrate=19200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # Litescope for analyzing the BIST output
        # --------------------
        self.submodules.io = LiteScopeIO(8)
        for i in range(8):
            try:
                self.comb += platform.request("user_led", i).eq(self.io.output[i])
            except:
                pass

        analyzer_signals = [
            self.spiflash.bus,
        #    self.spiflash.cs_n,
        #    self.spiflash.clk,
        #    self.spiflash.dq_oe,
        #    self.spiflash.dqi,
        #    self.spiflash.sr,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 1024)

    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)


SoC = MemTestSoC
