from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import IceStormProgrammer


_io = [
    ("user_led", 0, Pins("C10"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("A10"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("D7"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("D6"), IOStandard("LVCMOS33")),
    ("user_led", 4, Pins("A7"), IOStandard("LVCMOS33")),
    ("user_led", 5, Pins("C7"), IOStandard("LVCMOS33")),
    ("user_led", 6, Pins("A4"), IOStandard("LVCMOS33")),
    ("user_led", 7, Pins("C4"), IOStandard("LVCMOS33")),

    # row drivers
    # top to bottom
    # C5 A6 D10 A12
    ("user_led", 8, Pins("C5"), IOStandard("LVCMOS33")),
    ("user_led", 9, Pins("A6"), IOStandard("LVCMOS33")),
    ("user_led", 10, Pins("D10"), IOStandard("LVCMOS33")),
    ("user_led", 11, Pins("A12"), IOStandard("LVCMOS33")),

    ("rgb_leds", 0, # you must use the ground pin between p14 and n14
        # Subsignal("r", Pins("G6 G3 J3 K1")),
        # Subsignal("g", Pins("F6 J4 J2 H6")),
        # Subsignal("b", Pins("E1 G4 H4 K2")),
        IOStandard("LVCMOS33")
    ),

    ("user_btn", 0, Pins("A5"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("A11"), IOStandard("LVCMOS33")),
    ("user_btn", 2, Pins("C6"), IOStandard("LVCMOS33")),
    ("user_btn", 3, Pins("C11"), IOStandard("LVCMOS33")),

    # Piezo - Two pins drive the piezo
    # M12 M6

    ("serial", 0,
        Subsignal("rx", Pins("P2")),
        Subsignal("tx", Pins("P3"), Misc("PULLUP")),
        IOStandard("LVCMOS33"),
    ),

    ("serial", 1,
        Subsignal("rx", Pins("P4")),
        Subsignal("tx", Pins("P5"), Misc("PULLUP")),
        IOStandard("LVCMOS33"),
    ),


    ("spiflash", 0,
        Subsignal("cs_n", Pins("P13"), IOStandard("LVCMOS33")),
        Subsignal("clk", Pins("P12"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("M11"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("P11"), IOStandard("LVCMOS33")),
    ),

    ("clk12", 0, Pins("P7"), IOStandard("LVCMOS33"))
]


class Platform(LatticePlatform):
    default_clk_name = "clk12"
    default_clk_period = 83.333

    # gateware_size = 3*64*1024 # from icefundocs first 3 64k sectors reserved for FPGA
    gateware_size = 0x28000

    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    spiflash_model = "at25sf081"
    spiflash_read_dummy_bits = 8
    spiflash_clock_div = 2
    megabits = 8
    spiflash_total_size = int((megabits/8)*1024*1024)
    spiflash_page_size = 256
    spiflash_sector_size = 64*1024

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-hx8k-cb132", _io,
                                 toolchain="icestorm")

    def create_programmer(self):
        raise NotImplementedError()
        # return IceStormProgrammer()
