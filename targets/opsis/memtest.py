from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

from litescope import LiteScopeAnalyzer

from gateware.memtest import LiteDRAMBISTCheckerScope

from targets.utils import csr_map_update
from targets.opsis.net import NetSoC as BaseSoC


class MemTestSoC(BaseSoC):
    csr_peripherals = (
        "generator",
        "checker",
        "checker_scope",
        "analyzer",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.generator = LiteDRAMBISTGenerator(self.sdram.crossbar.get_port(mode="write", dw=32), random=False)
        self.submodules.checker = LiteDRAMBISTChecker(self.sdram.crossbar.get_port(mode="read", dw=32, reverse=True), random=False)
        self.submodules.checker_scope = LiteDRAMBISTCheckerScope(self.checker)

        analyzer_signals = self.checker_scope.signals()

        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 1024)

    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)


SoC = MemTestSoC
