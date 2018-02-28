from migen import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut

from targets.utils import csr_map_update
from targets.opsis.net import NetSoC as BaseSoC


class GPIO2TOFE(Module):
    def __init__(self, tofe):
        self.layout = tofe.layout
        for name, size in self.layout:
            setattr(self.submodules, name, GPIOOut(getattr(tofe, name)))

    def get_csrs(self):
        csrs = []
        for name, size in self.layout:
            io_csr = getattr(self, name).get_csrs()
            assert len(io_csr) == 1
            io_csr[0].name = name
            csrs += [io_csr[0]]
        return csrs


class AxiomSoC(BaseSoC):
    csr_peripherals = (
        "gpio",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, expansion='tofe2axiom', **kwargs)

        self.submodules.gpio = GPIO2TOFE(platform.request("tofe", 0))


SoC = AxiomSoC
