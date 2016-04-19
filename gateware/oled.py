from litex.gen import *

from litex.soc.interconnect.csr import *
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.gpio import GPIOOut


class OLED(Module, AutoCSR):
    def __init__(self, pads):
        spi_pads = Record([("cs_n", 1), ("clk", 1), ("mosi", 1)])
        self.submodules.spi = SPIMaster(spi_pads, 8, div=16, cpha=1)
        self.comb += [
            pads.sclk.eq(spi_pads.clk),
            pads.sdin.eq(spi_pads.mosi)
        ]
        self.submodules.gpio = GPIOOut(Cat(pads.res, pads.dc, pads.vbat, pads.vdd))
