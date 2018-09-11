from litex.soc.cores import uart
from litex.soc.cores.uart import UARTWishboneBridge

from litedram.frontend.bist import LiteDRAMBISTGenerator, LiteDRAMBISTChecker

from litescope import LiteScopeAnalyzer
from litescope import LiteScopeIO

from gateware.memtest import LiteDRAMBISTCheckerScope
from gateware import shared_uart

from targets.utils import csr_map_update
from targets.mimasv2.base import BaseSoC


class MemTestSoC(BaseSoC):
    csr_peripherals = (
        "generator",
        "checker",
        "checker_scope",
        "analyzer",
        "io",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, with_uart=False, **kwargs)

        # Memory test BIST
        self.submodules.generator = LiteDRAMBISTGenerator(self.sdram.crossbar.get_port(mode="write", data_width=32))
        self.submodules.checker = LiteDRAMBISTChecker(self.sdram.crossbar.get_port(mode="read", data_width=32))
        self.submodules.checker_scope = LiteDRAMBISTCheckerScope(self.checker)

        # Litescope for analyzing the BIST output
        # --------------------
        # Dummy UART
        self.submodules.suart = shared_uart.SharedUART(self.clk_freq, 115200)
        self.submodules.uart = self.suart.uart

        self.submodules.uartbridge = UARTWishboneBridge(platform.request("serial"), self.clk_freq, baudrate=19200)
        self.add_wb_master(self.uartbridge.wishbone)

#        self.submodules.io = LiteScopeIO(8)
#        for i in range(8):
#            try:
#                self.comb += platform.request("user_led", i).eq(self.io.output[i])
#            except:
#                pass

        analyzer_signals = self.checker_scope.signals()
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 64)

    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)


SoC = MemTestSoC
