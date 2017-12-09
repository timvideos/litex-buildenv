# Support for the Numato Saturn (http://numato.com/product/saturn-spartan-6-fpga-development-board-with-ddr-sdram)
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

#FIXME:
#this is for the LX45 version
#check on "no connect pins" for LX9 and LX25

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
    )
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

#   FPGA P3     _connector "P3"             FPGA P2       _connector P2
#    5           0 G13                       7               0 K12
#    6           1 H12                       8               1 K13
#    7           2 K14                      11               2 L14
#    8           3 J13                      12               3 M13
#    9           4 H16                      15               4 M14
#   10           5 H15                      16               5 N14
#   11           6 H14                      17               6 L12
#   12           7 H13                      18               7 L13
#   13           8 G14                      19               8 L15
#   14           9 F14                      20               9 L16
#   15          10 G18                      21              10 K15
#   16          11 G16                      22              11 K16
#   17          12 F16                      23              12 N15
#   18          13 F15                      24              13 N16
#   19          14 F18                      25              14 T17
#   20          15 F17                      26              15 T18
#   21          16 E18                      27              16 P15
#   22          17 E16                      28              17 P16
#   23          18 D18                      29              18 U16
#   24          19 D17                      30              19 V16
#   25          20 C18                      31              20 U17
#   26          21 C17                      32              21 U18
#   27          22 A16                      33              22 T14
#   28          23 B16                      34              23 V14
#   29          24 A15                      35              24 U15
#   30          25 C15                      36              25 V15
#   31          26 C14                      37              26 T12
#   32          27 D14                      38              27 V12
#   33          28 A14                      39              28 U13
#   34          29 B14                      40              29 V13
#   35          30 E13                      41              30 R11
#   36          31 F13                      42              31 T11
#   37          32 A13                      43              32 M11
#   38          33 C13                      44              33 N11
#   43          34 A12                      53              34 N10
#   44          35 B12                      54              35 P11
#   47          36 C11                      55              36 U11
#   48          37 D11                      56              37 V11
#   55          38 A11                      57              38 R10
#   56          39 B11                      58              39 T10
#   57          40 A10                      59              40 M10
#   58          41 C10                      60              41  N9
#   59          42  F9                      61              42  T9
#   60          43  G9                      62              43  V9
#   61          44  C9                      63              44  R8
#   62          45  D9                      64              45  T8
#   63          46  A9                      65              46  N7
#   64          47  B9                      66              47  P8
#   69          48  C8                      67              48  M8
#   70          49  D8                      68              49  N8
#   71          50  A8                      69              50  U7
#   72          51  B8                      70              51  V7
#   75          52  A7                      71              52  U8
#   76          53  C7                      72              53  V8
#   77          54  A6                      73              54  R7
#   78          55  B6                      74              55  T7
#   79          56  C6                      75              56  N6
#   80          57  D6                      76              57  P7
#   81          58  A5                      77              58  N5
#   82          59  C5                      78              59  P6
#   83          60  A4                      79              60  T6
#   84          61  B4                      80              61  V6
#   85          62  A3                      81              62  R5
#   86          63  B3                      82              63  T5
#   87          64  A2                      83              64  U5
#   88          65  B2                      84              65  V5
#                                           85              66  R3
#                                           86              67  T3
#                                           87              68  T4
#                                           88              69  V4

class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.00

    def __init__(self):
        XilinxPlatform.__init__(self, "xc6slx45-2csg324", _io, _connectors)
