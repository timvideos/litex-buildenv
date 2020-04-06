from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

class _CRG(Module):
    def __init__(self, platform):
        clk16 = platform.request("clk16")

        self.clock_domains.cd_sys = ClockDomain()
        self.reset = Signal()

        # FIXME: Use PLL, increase system clock to 32 MHz, pending nextpnr
        # fixes.
        self.comb += self.cd_sys.clk.eq(clk16)

        # POR reset logic- POR generated from sys clk, POR logic feeds sys clk
        # reset.
        self.clock_domains.cd_por = ClockDomain()
        reset_delay = Signal(12, reset=4095)
        self.comb += [
            self.cd_por.clk.eq(self.cd_sys.clk),
            self.cd_sys.rst.eq(reset_delay != 0)
        ]
        self.sync.por += \
            If(reset_delay != 0,
                reset_delay.eq(reset_delay - 1)
            )
        self.specials += AsyncResetSynchronizer(self.cd_por, self.reset)

