"""Built In Self Test (BIST) modules for testing liteDRAM functionality."""

from migen import *


class LiteDRAMBISTCheckerScope(Module):
    """Easy scope access to important signals of LiteDRAMBISTChecker."""

    def __init__(self, checker):
        core = checker.core
        self.data_error = Signal()
        self.data_address = Signal(core.data_counter.nbits)
        self.data_expected = Signal(core.dma.source.data.nbits)
        self.data_actual = Signal(core.dma.source.data.nbits)

        self.comb += [
            self.data_error.eq(core.dma.source.valid &
                               (self.data_actual != self.data_expected)),
            self.data_address.eq(core.base + core.data_counter),
            self.data_actual.eq(core.dma.source.data),
            self.data_expected.eq(core.gen.o),
        ]

    def signals(self):
        return [
            self.data_error,
            self.data_address,
            self.data_expected,
            self.data_actual,
        ]
