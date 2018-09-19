from litedram.frontend.bist import LiteDRAMBISTGenerator, LiteDRAMBISTChecker

from targets.utils import csr_map_update
from targets.sim.net import NetSoC as BaseSoC


class MemTestSoC(BaseSoC):
    csr_peripherals = (
        "generator",
        "checker",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        self.submodules.generator = LiteDRAMBISTGenerator(
            self.sdram.crossbar.get_port(mode="write"),
        )
        #self.submodules.checker = LiteDRAMBISTChecker(
        #    self.sdram.crossbar.get_port(mode="read", data_width=16),
        #    clock_domain="hdmi_out1_pix",
        #)
        self.submodules.checker = LiteDRAMBISTChecker(
            self.sdram.crossbar.get_port(mode="read"),
        #   cd="hdmi_out1_pix"),
        )


SoC = MemTestSoC
