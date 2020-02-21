# Support for the MATRIX Voice
# https://www.matrix.one/products/voice
# Author: Andres Calderon <andres.calderon@admobilize.com>
# FPGA: Spartan 6 xc6slx9-2-ftg256
# Copyright 2020 MATRIX Labs
# License: BSD

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

_io = [
    ("clk50", 0, Pins("T7"), IOStandard("LVCMOS33")),
#   RPI_GPIO26
    ("cpu_reset", 0, Pins("N6"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    ("serial", 0,
        Subsignal("tx", Pins("B12"), IOStandard("LVCMOS33"),
                  Misc("SLEW=FAST")),
        Subsignal("rx", Pins("A12"), IOStandard("LVCMOS33"),
                  Misc("SLEW=FAST"))),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("T3")),
        Subsignal("clk", Pins("R11")),
        Subsignal("mosi", Pins("T10")),
        Subsignal("miso", Pins("P10"), Misc("PULLUP")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")),

    ("ddram_clock", 0,
        Subsignal("p", Pins("G12")),
        Subsignal("n", Pins("H11")),
        IOStandard("DIFF_SSTL18_II"), Misc("IN_TERM=NONE")),

    ("ddram", 0,
        Subsignal(
            "a", 
#                   0   1   2   3   4   5   6   7   8   9  10  11  12 
            Pins("H15 H16 F16 H13 C16 J11 J12 F15 F13 F14 C15 G11 D16"), 
            IOStandard("SSTL18_II")
        ),
        Subsignal("ba", Pins("G14 G16"), IOStandard("SSTL18_II")),
        Subsignal("cke", Pins("D14"), IOStandard("SSTL18_II")),
        Subsignal("ras_n", Pins("J13"), IOStandard("SSTL18_II")),
        Subsignal("cas_n", Pins("K14"), IOStandard("SSTL18_II")),
        Subsignal("we_n", Pins("E15"), IOStandard("SSTL18_II")),
        Subsignal(
            "dq", 
#                   0   1   2   3   4   5   6   7   8   9   10   11   12   13   14   15  
            Pins("L14 L16 M15 M16 J14 J16 K15 K16 P15 P16  R15  R16  T14  T13  R12  T12"),
            IOStandard("SSTL18_II")
        ),
        Subsignal("dqs", Pins("R14 N14"), IOStandard("DIFF_SSTL18_II")),
        Subsignal("dqs_n", Pins("T15 N16"), IOStandard("DIFF_SSTL18_II")),
        Subsignal("dm", Pins("K12 K11"), IOStandard("SSTL18_II")),
        Subsignal("odt", Pins("H14"), IOStandard("SSTL18_II"))
    ),

    # LED
    ("user_led", 0, Pins("T5"), IOStandard("LVCMOS33"), Drive(8)),
]

_connectors = [
    ("P2", "G1 G3 H1 H2 J1 J3 K1 K2 L1 M1 M2 N1 P1 P2 R1 R2"),
]

class Platform(XilinxPlatform):
    name = "matrix_voice"
    default_clk_name = "clk50"
    default_clk_period = 20

    gateware_size = 0x180000

    spiflash_model = "25l6405"
    spiflash_read_dummy_bits = 4
    spiflash_clock_div = 4
    spiflash_total_size = int((64/8)*1024*1024) # 64Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    def __init__(self, device="xc6slx9", programmer="xc3sprog"):
        XilinxPlatform.__init__(self, device+"-2-ftg256", _io, _connectors)
        self.programmer = programmer

    def create_programmer(self):
        proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
        if self.programmer == "xc3sprog":
            return XC3SProg("matrix_voice", proxy)
        else:
            raise ValueError("{} programmer is not supported".format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        try:
            self.add_period_constraint(self.lookup_request("clk50", 0), 20)
        except ConstraintError:
            pass
