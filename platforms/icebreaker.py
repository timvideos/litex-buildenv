from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import IceStormProgrammer


_io = [
    # HACK: Use icefeather pins
    ("user_led_n",    0, Pins("47"), IOStandard("LVCMOS33")),
    ("user_led_n",    1, Pins("41"), IOStandard("LVCMOS33")),
    # Color-specific aliases
    ("user_ledr_n",   0, Pins("47"), IOStandard("LVCMOS33")),
    ("user_ledg_n",   0, Pins("41"), IOStandard("LVCMOS33")),
    ("user_btn_n", 0, Pins("10"), IOStandard("LVCMOS33")),
    
    # HACK: Replace UART with icefeather pins
    #("serial", 0,
    #    Subsignal("rx", Pins("6")),
    #    Subsignal("tx", Pins("9"), Misc("PULLUP")),
    #    IOStandard("LVCMOS33")
    #),

    ("serial", 0,
        Subsignal("rx", Pins("23")),
        Subsignal("tx", Pins("21"), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),

    ("spiflash", 0,
        Subsignal("cs_n",      Pins("16"), IOStandard("LVCMOS33")),
        Subsignal("clk",       Pins("15"), IOStandard("LVCMOS33")),
        Subsignal("miso",        Pins("17"), IOStandard("LVCMOS33")),
        Subsignal("mosi",        Pins("14"), IOStandard("LVCMOS33")),
        Subsignal("wp",      Pins("12"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("13"), IOStandard("LVCMOS33")),
    ),

    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("16"), IOStandard("LVCMOS33")),
        Subsignal("clk",  Pins("15"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("14 17 12 13"), IOStandard("LVCMOS33")),
    ),

    ("clk12", 0, Pins("35"), IOStandard("LVCMOS33"))
]

_connectors = [
    ("RGBLED", "39 40 41"),
]

rgb_led = [
    ("rgbled", 0, 
     Subsignal("rgb0", Pins("RGBLED:0")),
     Subsignal("rgb1", Pins("RGBLED:1")),
     Subsignal("rgb2", Pins("RGBLED:2")),
     IOStandard("LVCMOS33")
    ),
]


class Platform(LatticePlatform):
    default_clk_name = "clk12"
    default_clk_period = 83.333

    gateware_size = 0x20000

    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    spiflash_model = "n25q128"
    spiflash_read_dummy_bits = 8
    spiflash_clock_div = 2
    spiflash_total_size = int((128/8)*1024*1024) # 128Mbit
    spiflash_page_size = 256
    # Winbond calls 32kb/64kb sectors "blocks".
    spiflash_sector_size = 0x10000

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-up5k-sg48", _io, _connectors,
                                 toolchain="icestorm")

    def create_programmer(self):
        return IceStormProgrammer()
