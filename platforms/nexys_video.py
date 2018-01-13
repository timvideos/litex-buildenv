# This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [
    ("user_led", 0, Pins("T14"), IOStandard("LVCMOS25")),
    ("user_led", 1, Pins("T15"), IOStandard("LVCMOS25")),
    ("user_led", 2, Pins("T16"), IOStandard("LVCMOS25")),
    ("user_led", 3, Pins("U16"), IOStandard("LVCMOS25")),
    ("user_led", 4, Pins("V15"), IOStandard("LVCMOS25")),
    ("user_led", 5, Pins("W16"), IOStandard("LVCMOS25")),
    ("user_led", 6, Pins("W15"), IOStandard("LVCMOS25")),
    ("user_led", 7, Pins("Y13"), IOStandard("LVCMOS25")),

    ("user_sw", 0, Pins("E22"), IOStandard("LVCMOS25")),
    ("user_sw", 1, Pins("F21"), IOStandard("LVCMOS25")),
    ("user_sw", 2, Pins("G21"), IOStandard("LVCMOS25")),
    ("user_sw", 3, Pins("G22"), IOStandard("LVCMOS25")),
    ("user_sw", 4, Pins("H17"), IOStandard("LVCMOS25")),
    ("user_sw", 5, Pins("J16"), IOStandard("LVCMOS25")),
    ("user_sw", 6, Pins("K13"), IOStandard("LVCMOS25")),
    ("user_sw", 7, Pins("M17"), IOStandard("LVCMOS25")),


    ("user_btn", 0, Pins("B22"), IOStandard("LVCMOS25")),
    ("user_btn", 1, Pins("D22"), IOStandard("LVCMOS25")),
    ("user_btn", 2, Pins("C22"), IOStandard("LVCMOS25")),
    ("user_btn", 3, Pins("D14"), IOStandard("LVCMOS25")),
    ("user_btn", 4, Pins("F15"), IOStandard("LVCMOS25")),
    ("user_btn", 5, Pins("G4"),  IOStandard("LVCMOS25")),

    ("vadj", 0, Pins("AA13 AB17"), IOStandard("LVCMOS25")),

    ("oled", 0,
        Subsignal("dc",   Pins("W22")),
        Subsignal("res",  Pins("U21")),
        Subsignal("sclk", Pins("W21")),
        Subsignal("sdin", Pins("Y22")),
        Subsignal("vbat", Pins("P20")),
        Subsignal("vdd",  Pins("V22")),
        IOStandard("LVCMOS33")
    ),

    ("clk100", 0, Pins("R4"), IOStandard("LVCMOS33")),

    ("cpu_reset", 0, Pins("G4"), IOStandard("LVCMOS15")),


    # P22 - QSPI_DQ0 - MOSI
    # R22 - QSPI_DQ1 - MISO
    # P21 - QSPI_DQ2 - ~WP
    # R21 - QSPI_DQ3 - ~HOLD
    # T19 - QSPI_CS  - ~CS
    # L12 - CCLK
    ("spiflash_4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("T19")),
        Subsignal("dq", Pins("P22", "R22", "P21", "R21")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash_1x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("T19")),
        Subsignal("mosi", Pins("P22")),
        Subsignal("miso", Pins("R22")),
        Subsignal("wp", Pins("P21")),
        Subsignal("hold", Pins("R21")),
        IOStandard("LVCMOS33")
    ),

    ("serial", 0,
        Subsignal("tx", Pins("AA19")),
        Subsignal("rx", Pins("V18")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "M2 M5 M3 M1 L6 P1 N3 N2",
            "M6 R1 L5 N5 N4 P2 P6"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("L3 K6 L4"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("J4"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("K3"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("L1"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("G3 F1"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "G2 H4 H5 J1 K1 H3 H2 J5",
            "E3 B2 F3 D2 C2 A1 E2 B1"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_p", Pins("K2 E1"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("J2 D1"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("P5"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("P4"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("J6"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("K4"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("G1"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),

    ("eth_clocks", 0,
        Subsignal("tx", Pins("AA14")),
        Subsignal("rx", Pins("V13")),
        IOStandard("LVCMOS25")
    ),
    ("eth", 0,
        Subsignal("rst_n", Pins("U7"), IOStandard("LVCMOS33")),
        Subsignal("int_n", Pins("Y14")),
        Subsignal("mdio", Pins("Y16")),
        Subsignal("mdc", Pins("AA16")),
        Subsignal("rx_ctl", Pins("W10")),
        Subsignal("rx_data", Pins("AB16 AA15 AB15 AB11")),
        Subsignal("tx_ctl", Pins("V10")),
        Subsignal("tx_data", Pins("Y12 W12 W11 Y11")),
        IOStandard("LVCMOS25")
    ),

    ("hdmi_in", 0,
        Subsignal("clk_p", Pins("V4"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("W4"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("Y3"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("AA3"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("W2"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("Y2"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("U2"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("V2"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("Y4"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("AB5"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("AB12"), IOStandard("LVCMOS25")),
        Subsignal("cec", Pins("AA5"), IOStandard("LVCMOS33")),  # FIXME
        Subsignal("txen", Pins("R3"), IOStandard("LVCMOS33")),  # FIXME
    ),

    ("hdmi_out", 0,
        Subsignal("clk_p", Pins("T1"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("U1"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("W1"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("Y1"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("AA1"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("AB1"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("AB3"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("AB2"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("U3"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("V3"), IOStandard("LVCMOS33")),
        Subsignal("cec", Pins("AA4"), IOStandard("LVCMOS33")),  # FIXME
        Subsignal("hdp", Pins("AB13"), IOStandard("LVCMOS25")), # FIXME
    ),
]

_connectors = [
    ("LPC", {
        "GBTCLK0_M2C_P": "F10",
        "GBTCLK0_M2C_N": "E10",
        "LA01_CC_P": "J20",
        "LA01_CC_N": "J21",
        "LA05_P": "M21",
        "LA05_N": "L21",
        "LA09_P": "H20",
        "LA09_N": "G20",
        "LA13_P": "K17",
        "LA13_N": "J17",
        "LA17_CC_P": "B17",
        "LA17_CC_N": "B18",
        "LA23_P": "B21",
        "LA23_N": "A21",
        "LA26_P": "F18",
        "LA26_N": "E18",
        "CLK0_M2C_P": "J19",
        "CLK0_M2C_N": "A19",
        "LA02_P": "M18",
        "LA02_N": "L18",
        "LA04_P": "N20",
        "LA04_N": "M20",
        "LA07_P": "M13",
        "LA07_N": "L13",
        "LA11_P": "L14",
        "LA11_N": "L15",
        "LA15_P": "L16",
        "LA15_N": "K16",
        "LA19_P": "A18",
        "LA19_N": "A19",
        "LA21_P": "E19",
        "LA21_N": "D19",
        "LA24_P": "B15",
        "LA24_N": "B16",
        "LA28_P": "C13",
        "LA28_N": "B13",
        "LA30_P": "A13",
        "LA30_N": "A14",
        "LA32_P": "A15",
        "LA32_N": "A16",
        "LA06_P": "N22",
        "LA06_N": "M22",
        "LA10_P": "K21",
        "LA10_N": "K22",
        "LA14_P": "J22",
        "LA14_N": "H22",
        "LA18_CC_P": "D17",
        "LA18_CC_N": "C17",
        "LA27_P": "B20",
        "LA27_N": "A20",
        "CLK1_M2C_P": "C18",
        "CLK1_M2C_N": "C19",
        "LA00_CC_P": "K18",
        "LA00_CC_N": "K19",
        "LA03_P": "N18",
        "LA03_N": "N19",
        "LA08_P": "M15",
        "LA08_N": "M16",
        "LA12_P": "L19",
        "LA12_N": "L20",
        "LA16_P": "G17",
        "LA16_N": "G18",
        "LA20_P": "F19",
        "LA20_N": "F20",
        "LA22_P": "E21",
        "LA22_N": "D21",
        "LA25_P": "F16",
        "LA25_N": "E17",
        "LA29_P": "C14",
        "LA29_N": "C15",
        "LA31_P": "E13",
        "LA31_N": "E14",
        "LA33_P": "F13",
        "LA33_N": "F14",
        }
    )
]

_hdmi_infos = {
    "HDMI_OUT0_MNEMONIC": "TX1",
    "HDMI_OUT0_DESCRIPTION" : (
      "  FIXME in platforms/nexys_video.py\\r\\n"
    ),

    "HDMI_IN0_MNEMONIC": "RX1",
    "HDMI_IN0_DESCRIPTION" : (
      "  FIXME in platforms/nexys_video.py\\r\\n"
    ),
}

class Platform(XilinxPlatform):
    name = "nexys_video"
    default_clk_name = "clk100"
    default_clk_period = 10.0
    hdmi_infos = _hdmi_infos

    # From https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf
    # 77,845,216 bits == 9730652 == 0x947a5c -- Therefore 0x1000000
    gateware_size = 0x1000000

    # Spansion S25FL256S (ID 0x00190201)
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((256/8)*1024*1024) # 256Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000
    spiflash_model = "n25q128"

    def __init__(self, toolchain="vivado", programmer="openocd"):
        XilinxPlatform.__init__(self, "xc7a200t-sbg484-1", _io, _connectors,
                                toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 35]")


    def create_programmer(self):
        if self.programmer == "openocd":
            proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
            return OpenOCD(config="board/digilent_nexys_video.cfg", flash_proxy_basename=proxy)
        elif self.programmer == "xc3sprog":
            return XC3SProg("nexys4")
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4") # FIXME: Spansion S25FL256S
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        try:
            self.add_period_constraint(self.lookup_request("eth_clocks").rx, 8.0)
        except ConstraintError:
            pass
