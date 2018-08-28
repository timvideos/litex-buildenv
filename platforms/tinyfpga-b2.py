#!/usr/bin/env python3

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.build.lattice.programmer import TinyFpgaBProgrammer


_io = [
    ("clk16", 0, Pins("B4"), IOStandard("LVCMOS33")),
    ("rst", 0, Pins("E1"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("A1")),
        Subsignal("rx", Pins("A2")),
        IOStandard("LVCMOS33")
    ),
    ("user_led", 0, Pins("B1"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("C1"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("D1"), IOStandard("LVCMOS33")),
]


class Platform(LatticePlatform):
    def __init__(self):
        LatticePlatform.__init__(self, "ice40-lp8k-cm81", _io, toolchain="icestorm")

    def create_programmer(self):
        return TinyFpgaBProgrammer()
