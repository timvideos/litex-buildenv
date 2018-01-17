# Support for the Numato Galatea - PCI Express Spartan 6 Development Board
# https://numato.com/product/galatea-pci-express-spartan-6-fpga-development-board

from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, iMPACT

from third_party.litex.litex.build.xilinx.programmer import XC3SProg

_io = [
    # ---------------------- Clocks ---------------------------
    # Clock U18 - 100MHz - CMOS Crystal Oscillator
    # NET "CLK1"               LOC = "AB13"   | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;   # Bank = 0
    ("clk100", 0, Pins("G9"), IOStandard("LVCMOS33")),
    # Clock U19 - 100MHz - CMOS Crystal Oscillator
    # NET "CLK2"               LOC = "Y13"    | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;   # Bank = 2
    ("clk2", 0, Pins("Y13"), IOStandard("LVCMOS33")),
    # Clock U17 - 100MHz - CMOS Crystal Oscillator
    # NET "CLK3"               LOC = "AB13"   | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;   # Bank = 2
    ("clk3", 0, Pins("AB13"), IOStandard("LVCMOS33")),

    # Clock U21 SMA Clock
    # NET "EXT_CLK1"           LOC = "U12"    | IOSTANDARD = "LVCMOS33";                      # Bank = 2

    # Clock U6 SMA Clock
    # NET "EXT_CLK2"           LOC = "T12"    | IOSTANDARD = "LVCMOS33";                      # Bank = 2

    # SW1
    #NET "RST_N"              LOC = "AB19"   | IOSTANDARD = "LVCMOS33" | PULLUP ;             # Bank = 2
    ("cpu_reset", 0, Pins("AB19"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    # ---------------------- UART -----------------------------
    #NET "UART_RX"            LOC = "V17"    | IOSTANDARD = "LVCMOS33";                       # Bank = 2
    #NET "UART_TX"            LOC = "W18"    | IOSTANDARD = "LVCMOS33";                       # Bank = 2
    ("serial", 0,
     Subsignal("rx", Pins("V17"), IOStandard("LVCMOS33")),
     Subsignal("tx", Pins("W18"), IOStandard("LVCMOS33")),
    ),
    #                                                             SPI Flash                                                                                #
    #NET "SPI_Flash_SCK"      LOC = "Y20"    | IOSTANDARD = "LVCMOS33";                       # Bank = 2
    #NET "SPI_Flash_MISO"     LOC = "T14"    | IOSTANDARD = "LVCMOS33";                       # Bank = 2
    #NET "SPI_Flash_MOSI"     LOC = "AB20"   | IOSTANDARD = "LVCMOS33";                       # Bank = 2
    #NET "SPI_Flash_SS"       LOC = "AA3"    | IOSTANDARD = "LVCMOS33";                       # Bank = 2

    ## onBoard Quad-SPI Flash
    ## N25Q128A13ESE40E - 128 Mb QSPI flash memory

    #QSPI_FLASH_SCLK	Y20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO0		AB20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO1		AA20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO2		R13	LVCMOS33	16	FAST
    #QSPI_FLASH_IO3		T14	LVCMOS33	16	FAST
    #QSPI_FLASH_SS		AA3	LVCMOS33	16	FAST

    ("spiflash1x", 0,
        #NET "SPI_Flash_SCK"      LOC = "Y20"    | IOSTANDARD = "LVCMOS33";                   # Bank = 2
        Subsignal("clk", Pins("Y20")),
        #NET "SPI_Flash_SS"       LOC = "AA3"    | IOSTANDARD = "LVCMOS33";                   # Bank = 2
        Subsignal("cs_n", Pins("AA3")),
        #NET "SPI_Flash_MISO"     LOC = "T14"    | IOSTANDARD = "LVCMOS33";                   # Bank = 2
        #NET "SPI_Flash_MOSI"     LOC = "AB20"   | IOSTANDARD = "LVCMOS33";                   # Bank = 2
        #Subsignal("dq", Pins("AB20", "AA20", "R13", "T14")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")
    ),

    ## DDR3 Chip:0
    # MT41J128M16JT-125:K - 16 Meg x 16 x 8 Banks - DDR3-1600 11-11-11
    # FBGA Code: D9PSL, Part Number: MT41J128M16 - http://www.micron.com/support/fbga
    ("ddram_clock", 0,
        Subsignal("p", Pins("K4")),
        Subsignal("n", Pins("K3")),
        IOStandard("DIFF_SSTL15_II"), Misc("IN_TERM=NONE")
    ),
    ("ddram", 0,
        Subsignal("cke", Pins("F2"), IOStandard("SSTL15_II")),
        Subsignal("ras_n", Pins("M5"), IOStandard("SSTL15_II")),
        Subsignal("cas_n", Pins("M4"), IOStandard("SSTL15_II")),
        Subsignal("we_n", Pins("H2"), IOStandard("SSTL15_II")),
        Subsignal("ba", Pins("J3 J1 H1"), IOStandard("SSTL15_II")),
        Subsignal("a", Pins("K2 K1 K5 M6 H3 L4 M3 K6 G3 G1 J4 E1 F1 J6 H5"), IOStandard("SSTL15_II")),
        Subsignal("dq", Pins(
                    "R3 R1 P2 P1 L3 L1 M2 M1",
                    "T2 T1 U3 U1 W3 W1 Y2 Y1"), IOStandard("SSTL15_II")),
        Subsignal("dqs", Pins("N3 V2"), IOStandard("DIFF_SSTL15_II")),
        Subsignal("dqs_n", Pins("N1 V1"), IOStandard("DIFF_SSTL15_II")),
        Subsignal("dm", Pins("N4 P3"), IOStandard("SSTL15_II")),
        Subsignal("odt", Pins("L6"), IOStandard("SSTL15_II")),
        Subsignal("reset_n", Pins("E3"), IOStandard("LVCMOS15")),
        Misc("SLEW=FAST"),
        Misc("VCCAUX_IO=HIGH")
    ),

    ## DDR3 Chip:1
    # MT41J128M16JT-125:K - 16 Meg x 16 x 8 Banks - DDR3-1600 11-11-11
    # FBGA Code: D9PSL, Part Number: MT41J128M16 - http://www.micron.com/support/fbga
    ("ddram_clock", 1,
     Subsignal("p", Pins("K20")),
     Subsignal("n", Pins("L19")),
     IOStandard("DIFF_SSTL15_II"), Misc("IN_TERM=NONE")
     ),
    ("ddram", 1,
     Subsignal("cke", Pins("F21"), IOStandard("SSTL15_II")),
     Subsignal("ras_n", Pins("K21"), IOStandard("SSTL15_II")),
     Subsignal("cas_n", Pins("K22"), IOStandard("SSTL15_II")),
     Subsignal("we_n", Pins("K19"), IOStandard("SSTL15_II")),
     Subsignal("ba", Pins("K17 L17 K18"), IOStandard("SSTL15_II")),
     Subsignal("a", Pins("H21 H22 G22 J20 H20 M20 M19 G20 E20 E22 J19 H19 F22 G19 F20"), IOStandard("SSTL15_II")),
     Subsignal("dq", Pins(
         "R20 R22 P21 P22 L20 L22 M21 M22",
         "T21 T22 U20 U22 W20 W22 Y21 Y22"), IOStandard("SSTL15_II")),
     Subsignal("dqs", Pins("N20 V21"), IOStandard("DIFF_SSTL15_II")),
     Subsignal("dqs_n", Pins("N22 V22"), IOStandard("DIFF_SSTL15_II")),
     Subsignal("dm", Pins("N19 P20"), IOStandard("SSTL15_II")),
     Subsignal("odt", Pins("J22"), IOStandard("SSTL15_II")),
     Subsignal("reset_n", Pins("H18"), IOStandard("LVCMOS15")),
     Misc("SLEW=FAST"),
     Misc("VCCAUX_IO=HIGH")
     ),
]

_connectors = []

class Platform(XilinxPlatform):
    name = "galatea"
    default_clk_name = "clk100"
    default_clk_period = 10.0

    # W25Q128FVEIG - component U3
    # 128M (16M x 8) - 104MHz
    # Pretends to be a Micron N25Q128 (ID 0x0018ba20)
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_model = "n25q128"
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((128/8)*1024*1024) # 128Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    # The Galatea has a XC6SLX45 which bitstream takes up ~12Mbit (1484472 bytes)
    # 0x200000 offset (16Mbit) gives plenty of space
    gateware_size = 0x200000

    def __init__(self, programmer="openocd"):
        # XC6SLX45T-3FGG484C
        XilinxPlatform.__init__(self,  "xc6slx45t-fgg484-3", _io, _connectors)
        self.programmer = programmer

        pins = {
          'ProgPin': 'PullUp',
          'DonePin': 'PullUp',
          'TckPin': 'PullNone',
          'TdiPin': 'PullNone',
          'TdoPin': 'PullNone',
          'TmsPin': 'PullNone',
          'UnusedPin': 'PullNone',
          }
        for pin, config in pins.items():
            self.toolchain.bitgen_opt += " -g %s:%s " % (pin, config)

        # FPGA AUX is connected to the 3.3V supply
        self.add_platform_command("""CONFIG VCCAUX="3.3";""")

    def create_programmer(self):
        if self.programmer == "xc3sprog":
            return XC3SProg(cable='xpc')
        elif self.programmer == "impact":
            return iMPACT()
        else:
            raise ValueError("{} programmer is not supported".format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)

        # The oscillator clock sources.
        try:
            self.add_period_constraint(self.lookup_request("clk100"), 10.0)
        except ConstraintError:
            pass
