# Support for the Numato Waxwing Spartan 6 Development Module
# https://numato.com/product/waxwing-spartan-6-fpga-development-board

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform


_io = [
    ("clk100", 0, Pins("V10"), IOStandard("LVTTL")),

    ("serial", 0,
        Subsignal("tx",  Pins("L18")),
        Subsignal("rx",  Pins("L17"), Misc("PULLUP")),
        Subsignal("cts", Pins("M16"), Misc("PULLUP")),
        Subsignal("rts", Pins("M18"), Misc("PULLUP")),
        IOStandard("LVTTL")
    ),

    #the board has a FTDI FT2232H
    ("usb_fifo", 0,
        Subsignal("data",  Pins("L17 L18 M16 M18 N17 N18 P17 P18")),
        Subsignal("rxf_n", Pins("K18")),
        Subsignal("txe_n", Pins("K17")),
        Subsignal("rd_n",  Pins("J18")),
        Subsignal("wr_n",  Pins("J16")),
        Subsignal("siwua", Pins("H18")),
        IOStandard("LVTTL"),
    ),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("V3")),
        Subsignal("clk",  Pins("R15")),
        Subsignal("mosi", Pins("R13")),
        Subsignal("miso", Pins("T13"), Misc("PULLUP")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")
    ),

    ("ddram_clock", 0,
        Subsignal("p", Pins("G3")),
        Subsignal("n", Pins("G1")),
        IOStandard("MOBILE_DDR")
    ),

    ("ddram", 0,
        Subsignal("a", Pins("J7 J6 H5 L7 F3 H4 H3 H6 D2 D1 F4 D3 G6")),
        Subsignal("ba", Pins("F2 F1")),
        Subsignal("cke", Pins("H7")),
        Subsignal("ras_n", Pins("L5")),
        Subsignal("cas_n", Pins("K5")),
        Subsignal("we_n", Pins("E3")),
        Subsignal("dq", Pins("L2 L1 K2 K1 H2 H1 J3 J1 M3 M1 N2 N1 T2 T1 U2 U1")),
        Subsignal("dqs", Pins("L4 P2")),
        Subsignal("dm", Pins("K3 K4")),
        IOStandard("MOBILE_DDR")
    ),

    # Small DIP switches
    # DP1 (user_sw:0) -> DP8 (user_sw:7)
    ("user_sw", 0, Pins("L17"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 1, Pins("C18"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 2, Pins("C17"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 3, Pins("G14"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    ("user_btn", 0, Pins("F14"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 1, Pins("A14"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 2, Pins("T6"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 3, Pins("R5"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 4, Pins("B14"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 5, Pins("V6"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 6, Pins("T5"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    # TODO: Check and confirm pin maps below are correct or not
    #
    ("vga_out", 0,
     Subsignal("hsync_n", Pins("T18"), IOStandard("LVCMOS33"),
               Misc("SLEW=FAST")),
     Subsignal("vsync_n", Pins("U16"), IOStandard("LVCMOS33"),
               Misc("SLEW=FAST")),
     Subsignal("r", Pins("P18 U18 U17"), IOStandard("LVCMOS33"),
               Misc("SLEW=FAST")),
     Subsignal("g", Pins("N15 N16 N14"), IOStandard("LVCMOS33"),
               Misc("SLEW=FAST")),
     Subsignal("b", Pins("V16 P17"), IOStandard("LVCMOS33"),
               Misc("SLEW=FAST"))),

    ("sevenseg", 0,
     Subsignal("segment7", Pins("G16"), IOStandard("LVCMOS33")),  # A
     Subsignal("segment6", Pins("L15"), IOStandard("LVCMOS33")),  # B
     Subsignal("segment5", Pins("L16"), IOStandard("LVCMOS33")),  # C
     Subsignal("segment4", Pins("K13"), IOStandard("LVCMOS33")),  # D
     Subsignal("segment3", Pins("K12"), IOStandard("LVCMOS33")),  # E
     Subsignal("segment2", Pins("G18"), IOStandard("LVCMOS33")),  # F
     Subsignal("segment1", Pins("F18"), IOStandard("LVCMOS33")),  # G
     Subsignal("segment0", Pins("L18"), IOStandard("LVCMOS33")),  # Dot
     Subsignal("enable0", Pins("F17"), IOStandard("LVCMOS33")),  # EN0
     Subsignal("enable1", Pins("L14"), IOStandard("LVCMOS33")),  # EN1
     Subsignal("enable2", Pins("M13"), IOStandard("LVCMOS33"))),  # EN2

    ("mmc", 0,
            Subsignal("dat", Pins("N10 P11 R8 T8"), IOStandard("LVCMOS33"),
                      Misc("SLEW=FAST")),

            Subsignal("cmd", Pins("T9"), IOStandard("LVCMOS33"),
                      Misc("SLEW=FAST")),

            Subsignal("clk", Pins("V9"), IOStandard("LVCMOS33"),
                      Misc("SLEW=FAST"))),

    ("eth_clocks", 0,
     Subsignal("tx", Pins("R10")),
     Subsignal("rx", Pins("T10")),
     IOStandard("LVCMOS33")
     ),
    ("eth", 0,
     Subsignal("rst_n", Pins("P18")),
     Subsignal("mdio", Pins("V16")),
     Subsignal("mdc", Pins("T18")),
     Subsignal("dv", Pins("N14")),
     Subsignal("rx_er", Pins("P16")),
     Subsignal("rx_data", Pins("U17 U18 M18 M16")),
     Subsignal("tx_en", Pins("M14")),
     Subsignal("tx_data", Pins("N16 N15 V12 T12")),
     Subsignal("col", Pins("U16")),
     Subsignal("crs", Pins("P17")),
     IOStandard("LVCMOS33")
     ),

    ("hdmi_out", 0,
     Subsignal("clk_p", Pins("C10"), IOStandard("TMDS_33")),
     Subsignal("clk_n", Pins("A10"), IOStandard("TMDS_33")),
     Subsignal("data0_p", Pins("C7"), IOStandard("TMDS_33")),
     Subsignal("data0_n", Pins("A7"), IOStandard("TMDS_33")),
     Subsignal("data1_p", Pins("B8"), IOStandard("TMDS_33")),
     Subsignal("data1_n", Pins("A8"), IOStandard("TMDS_33")),
     Subsignal("data2_p", Pins("D8"), IOStandard("TMDS_33")),
     Subsignal("data2_n", Pins("C8"), IOStandard("TMDS_33")),
     Subsignal("scl", Pins("C6"), IOStandard("I2C")),
     Subsignal("sda", Pins("D6"), IOStandard("I2C")),
     Subsignal("hpd_notif", Pins("D14"), IOStandard("LVCMOS33"))
     ),

    ("ac97", 0,
     Subsignal("sdo", Pins("B9"), IOStandard("LVCMOS33")),
     Subsignal("bit_clk", Pins("C9"), IOStandard("LVCMOS33")),
     Subsignal("sdi", Pins("A9"), IOStandard("LVCMOS33")),
     Subsignal("sync", Pins("D9"), IOStandard("LVCMOS33")),
     Subsignal("reset", Pins("C13"), IOStandard("LVCMOS33")),
     ),
]

_connectors = [
    ("P3", "G13 H12 K14 J13 H16 H15 H14 H13 G14 F14 G18 G16 F16 F15 F18" #15 pins
           "F17 E18 E16 D18 D17 C18 C17 A16 B16 A15 C15 C14 D14 A14 B14" #15 pins
           "E13 F13 A13 C13 A12 B12 C11 D11 A11 B11 A10 C10 F9 G9 C9 D9" #16 pins
           "A9 B9 C8 D8 A8 B8 A7 C7 A6 B6 C6 D6 A5 C5 A4 B4 A3 B3 A2 B2" #20 pins
    ),

    ("P2", "K12 K13 L14 M13 M14 N14 L12 L13 L15 L16 K15 K16 N15 N16 T17" #15 pins
           "T18 P15 P16 U16 V16 U17 U18 T14 V14 U15 V15 T12 V12 U13 V13" #15 pins
           "R11 T11 M11 N11 N10 P11 U11 V11 R10 T10 M10 N9 T9 V9 R8 T8"  #16 pins
           "N7 P8 M8 N8 U7 V7 U8 V8 R7 T7 N6 P7 N5 P6 T6 V6 R5 T5 U5"    #19 pins
           "V5 R3 T3 T4 V4"                                              # 5 pins
    )
]


class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.00

    def __init__(self):
        XilinxPlatform.__init__(self, "xc6slx45-2csg324", _io, _connectors)
