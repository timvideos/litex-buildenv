from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import TinyProgProgrammer

_io = [
    ("user_led", 0, Pins("B3"), IOStandard("LVCMOS33")),

    ("usb", 0,
        Subsignal("d_p", Pins("B4")),
        Subsignal("d_n", Pins("A4")),
        Subsignal("pullup", Pins("A3")),
        IOStandard("LVCMOS33")
    ),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("F7"), IOStandard("LVCMOS33")),
        Subsignal("clk", Pins("G7"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("G6"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("H7"), IOStandard("LVCMOS33")),
        Subsignal("wp", Pins("H4"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("J8"), IOStandard("LVCMOS33"))
    ),

    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("F7"), IOStandard("LVCMOS33")),
        Subsignal("clk", Pins("G7"), IOStandard("LVCMOS33")),
        Subsignal("dq", Pins("G6 H7 H4 J8"), IOStandard("LVCMOS33"))
    ),

    ("clk16", 0, Pins("B2"), IOStandard("LVCMOS33"))
]

_connectors = [
    # Putting the USB connector at top (similar to TinyFPGA BX documentation card).
    # A2-H2, Pins 1-13,  GPIO:0  --> GPIO:12 - Left side, starting at top going down.
    # H9-A6, Pins 14-24, GPIO:13 --> GPIO:23 - Right side, starting at bottom going up.
    ("GPIO", "A2 A1 B1 C2 C1 D2 D1 E2 E1 G2 H1 J1 H2 H9 D9 D8 C9 A9 B8 A8 B7 A7 B6 A6"),
    # G1-J2, Pins 25-31  EXTRA:0 --> EXTRA:6 - Pads on the bottom of the board.
    ("EXTRA", "G1 J3 J4 G9 J9 E8 J2")
]


class Platform(LatticePlatform):
    name = "tinyfpga_bx"
    default_clk_name = "clk16"
    default_clk_period = 62.5

    # TinyFPGA BX normally defines the user bitstream to begin at 0x28000
    # and user data to begin at 0x50000; follow the convention here.
    bootloader_size = 0x28000
    gateware_size = 0x50000 - bootloader_size

    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    spiflash_model = "m25p16"
    spiflash_read_dummy_bits = 8
    spiflash_clock_div = 2
    spiflash_total_size = int((8/8)*1024*1024) # 8Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-lp8k-cm81", _io, _connectors,
                                 toolchain="icestorm")

    def create_programmer(self):
        return TinyProgProgrammer()
