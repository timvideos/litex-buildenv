from litedram.frontend.bist import LiteDRAMBISTGenerator, LiteDRAMBISTChecker

from litescope import LiteScopeAnalyzer

from targets.utils import csr_map_update
from targets.opsis.net import NetSoC as BaseSoC


class MemTestSoC(BaseSoC):
    csr_peripherals = (
        "generator",
        "checker",
        "analyzer",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.generator = LiteDRAMBISTGenerator(self.sdram.crossbar.get_port(mode="write"))
        #self.submodules.checker = LiteDRAMBISTChecker(self.sdram.crossbar.get_port(mode="read", dw=16)) #, cd="hdmi_out1_pix"))
        self.submodules.checker = LiteDRAMBISTChecker(self.sdram.crossbar.get_port(mode="read")) #, cd="hdmi_out1_pix"))

        analyzer_signals = [
            self.checker.core.cmd_counter,
            self.checker.core.data_counter,
            self.checker.core.data_error,
            self.checker.core.dma.source.data,  # expected
            self.checker.core.gen.o,            # actual
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048)

    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)


SoC = MemTestSoC
