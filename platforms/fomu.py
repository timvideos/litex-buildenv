# Support for the Fomu
# More information can be found here https://github.com/im-tomu/foboot.git

from litex.build.lattice.platform import LatticePlatform
from litex.build.generic_platform import Pins, IOStandard, Misc, Subsignal

_io_evt = [
    ("serial", 0,
        Subsignal("rx", Pins("21")),
        Subsignal("tx", Pins("13"), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),
    ("usb", 0,
        Subsignal("d_p", Pins("34")),
        Subsignal("d_n", Pins("37")),
        Subsignal("pullup", Pins("35")),
        Subsignal("pulldown", Pins("36")),
        IOStandard("LVCMOS33")
    ),
    ("touch", 0,
        Subsignal("t1", Pins("48"), IOStandard("LVCMOS33")),
        Subsignal("t2", Pins("47"), IOStandard("LVCMOS33")),
        Subsignal("t3", Pins("46"), IOStandard("LVCMOS33")),
        Subsignal("t4", Pins("45"), IOStandard("LVCMOS33")),
    ),
    ("pmoda", 0,
        Subsignal("p1", Pins("28"), IOStandard("LVCMOS33")),
        Subsignal("p2", Pins("27"), IOStandard("LVCMOS33")),
        Subsignal("p3", Pins("26"), IOStandard("LVCMOS33")),
        Subsignal("p4", Pins("23"), IOStandard("LVCMOS33")),
    ),
    ("pmodb", 0,
        Subsignal("p1", Pins("48"), IOStandard("LVCMOS33")),
        Subsignal("p2", Pins("47"), IOStandard("LVCMOS33")),
        Subsignal("p3", Pins("46"), IOStandard("LVCMOS33")),
        Subsignal("p4", Pins("45"), IOStandard("LVCMOS33")),
    ),
    ("led", 0,
        Subsignal("rgb0", Pins("39"), IOStandard("LVCMOS33")),
        Subsignal("rgb1", Pins("40"), IOStandard("LVCMOS33")),
        Subsignal("rgb2", Pins("41"), IOStandard("LVCMOS33")),
    ),
    ("spiflash", 0,
        Subsignal("cs_n", Pins("16"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("15"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("17"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("14"), IOStandard("LVCMOS33")),
        Subsignal("wp",   Pins("18"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("19"), IOStandard("LVCMOS33")),
    ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("16"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("15"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("14 17 18 19"), IOStandard("LVCMOS33")),
    ),
    ("clk48", 0, Pins("44"), IOStandard("LVCMOS33"))
]
_io_dvt = [
    ("serial", 0,
        Subsignal("rx", Pins("C3")),
        Subsignal("tx", Pins("B3"), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),
    ("usb", 0,
        Subsignal("d_p", Pins("A1")),
        Subsignal("d_n", Pins("A2")),
        Subsignal("pullup", Pins("A4")),
        IOStandard("LVCMOS33")
    ),
    ("touch", 0,
        Subsignal("t1", Pins("E4"), IOStandard("LVCMOS33")),
        Subsignal("t2", Pins("D5"), IOStandard("LVCMOS33")),
        Subsignal("t3", Pins("E5"), IOStandard("LVCMOS33")),
        Subsignal("t4", Pins("F5"), IOStandard("LVCMOS33")),
    ),
    ("led", 0,
        Subsignal("rgb0", Pins("A5"), IOStandard("LVCMOS33")),
        Subsignal("rgb1", Pins("B5"), IOStandard("LVCMOS33")),
        Subsignal("rgb2", Pins("C5"), IOStandard("LVCMOS33")),
    ),
    ("spiflash", 0,
        Subsignal("cs_n", Pins("C1"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("D1"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("E1"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("F1"), IOStandard("LVCMOS33")),
        Subsignal("wp",   Pins("F2"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("B1"), IOStandard("LVCMOS33")),
    ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("C1"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("D1"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("F1 E1 F2 B1"), IOStandard("LVCMOS33")),
    ),
    ("clk48", 0, Pins("F4"), IOStandard("LVCMOS33"))
]
_io_pvt = _io_dvt
_io_hacker = [
    ("serial", 0,
        Subsignal("rx", Pins("C3")),
        Subsignal("tx", Pins("B3"), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),
    ("usb", 0,
        Subsignal("d_p", Pins("A4")),
        Subsignal("d_n", Pins("A2")),
        Subsignal("pullup", Pins("D5")),
        IOStandard("LVCMOS33")
    ),
    ("touch", 0,
        Subsignal("t1", Pins("F4"), IOStandard("LVCMOS33")),
        Subsignal("t2", Pins("E5"), IOStandard("LVCMOS33")),
        Subsignal("t3", Pins("E4"), IOStandard("LVCMOS33")),
        Subsignal("t4", Pins("F2"), IOStandard("LVCMOS33")),
    ),
    ("led", 0,
        Subsignal("rgb0", Pins("A5"), IOStandard("LVCMOS33")),
        Subsignal("rgb1", Pins("B5"), IOStandard("LVCMOS33")),
        Subsignal("rgb2", Pins("C5"), IOStandard("LVCMOS33")),
    ),
    ("spiflash", 0,
        Subsignal("cs_n", Pins("C1"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("D1"), IOStandard("LVCMOS33")),
        Subsignal("miso", Pins("E1"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("F1"), IOStandard("LVCMOS33")),
        Subsignal("wp",   Pins("A1"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("B1"), IOStandard("LVCMOS33")),
    ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("C1"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("D1"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("F1 E1"), IOStandard("LVCMOS33")),
    ),
    ("clk48", 0, Pins("F5"), IOStandard("LVCMOS33"))
]

_connectors = []

class Platform(LatticePlatform):
    default_clk_name = "clk48"
    default_clk_period = 20.833

    # From FPGA-TN-02001-30-iCE40-Programming-Configuration.pdf
    # Table 9.2. Bitstream Sizes for Different iCE40 FPGA Densities Used to Select a SPI Flash
    # iCE40UP 5K; 104161 (bytes); 833288(bits)
    # 104161 bytes == 0x196E1 -- Therefore 0x20000
    gateware_size = 0x20000
    # User bitstream starts at 0x40000 in Flash
    bootloader_size = 0x40000

    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    spiflash_model = "n25q32"
    spiflash_read_dummy_bits = 8
    spiflash_clock_div = 2
    spiflash_total_size = int((32/8)*1024*1024) # 32Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    def __init__(self, revision="pvt", toolchain="icestorm"):
        self.revision = revision
        if revision == "evt":
            LatticePlatform.__init__(self, "ice40-up5k-sg48", _io_evt, _connectors, toolchain="icestorm")
        elif revision == "dvt":
            LatticePlatform.__init__(self, "ice40-up5k-uwg30", _io_dvt, _connectors, toolchain="icestorm")
        elif revision == "pvt":
            LatticePlatform.__init__(self, "ice40-up5k-uwg30", _io_pvt, _connectors, toolchain="icestorm")
        elif revision == "hacker":
            LatticePlatform.__init__(self, "ice40-up5k-uwg30", _io_hacker, _connectors, toolchain="icestorm")
        else:
            raise ValueError("Unrecognized reivsion: {}.  Known values: evt, dvt, pvt, hacker".format(revision))

    def create_programmer(self):
        raise ValueError("programming is not supported")
