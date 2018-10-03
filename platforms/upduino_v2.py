#!/usr/bin/env python3

"""
[UPDuino V2](http://gnarlygrey.atspace.cc/development-platform.html#upduino_v2)

 * Lattice UltraPlus FPGA
   - 5.3K LUTs, 1Mb SPRAM, 120Kb DPRAM, 8 Multipliers
 * FTDI FT232H USB to SPI Device for FPGA programming
 * 12Mhz Crystal Oscillator Clock Source
 * 34 GPIO on 0.1” headers
 * SPI Flash, RGB LED, 3.3V and 1.2V Regulators

"""

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.build.lattice.programmer import IceStormProgrammer


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
        LatticePlatform.__init__(self, "ice40-up5k-sg48", _io, toolchain="icestorm")

    def create_programmer(self):
        return IceStormProgrammer()
