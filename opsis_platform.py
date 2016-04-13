from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, iMPACT

_tofe_io = {
    "diff_io_a0n" : "C18",
    "diff_io_a0p" : "D17",
    "diff_io_b0n" : "A20",
    "diff_io_b0p" : "B20",
    "diff_io_xn"  : "A19",
    "diff_io_xp"  : "C19",
    "diff_io_a1n" : "A18",
    "diff_io_a1p" : "B18",
    "diff_clk_xn" : "D19",
    "diff_clk_xp" : "D18",
    "diff_io_b1n" : "F17",
    "diff_io_b1p" : "G16",
    "diff_io_b2n" : "A17",
    "diff_io_b2p" : "C17",
    "diff_io_a2n" : "G15",
    "diff_io_a2p" : "H14",
    "diff_io_a3n" : "G13",
    "diff_io_a3p" : "H13",
    "diff_clk_b0p": "F16",
    "diff_clk_b0n": "E16",
    "diff_io_a0n" : "F15",
    "diff_io_a0p" : "F14",
    "diff_clk_b1n": "G11",
    "diff_clk_b1p": "H12",
    "diff_clk_a1n": "F10",
    "diff_clk_a1p": "G9",
    "diff_io_b3n" : "H11",
    "diff_io_b3p" : "H10",
    "diff_io_zn"  : "F9",
    "diff_io_zp"  : "G8",
    "diff_io_b5n" : "A5",
    "diff_io_b5p" : "C5",
    "diff_io_yn"  : "F8",
    "diff_io_yp"  : "F7",
    "diff_io_a5n" : "A4",
    "diff_io_a5p" : "C4",
    "diff_io_b6n" : "A3",
    "diff_io_b6p" : "B3",
    "diff_io_a4n" : "E6",
    "diff_io_a4p" : "E5",
    "diff_io_a6n" : "A2",
    "diff_io_a6p" : "B2",
    "diff_io_b4n" : "D5",
    "diff_io_b4p" : "D4",
    "pcie_reset"  : "D3"
}

_tofe_low_speed_io = {
    "tx" : "diff_io_xp",
    "rx" : "diff_io_xn",

    "d0" : "diff_io_yn",
    "d1" : "diff_io_b1p",
    "d2" : "diff_io_b1n",
    "d3" : "diff_io_b2p",
    "d4" : "diff_io_b2n",
    "d5" : "diff_io_yp",
    "d6" : "diff_io_b3n",
    "d7" : "diff_io_b3p",
    "d8" : "diff_clk_b0n",
    "d9" : "diff_clk_b0p",
    "d10": "diff_io_zn",
    "d11": "diff_io_zp",
    "d12": "diff_io_b4p",
    "d13": "diff_io_b4n",
    "d14": "diff_io_b5n",
    "d15": "diff_io_b6p",

    "led1": "diff_io_a5p",
    "led2": "diff_io_a5n",
    "led3": "diff_io_b6n",
    "led4": "diff_io_a6p",

    "sw1" : "diff_clk_b1p",
    "sw2" : "diff_clk_b1n",
    "sw3" : "diff_clk_a1p",
    "sw4" : "diff_clk_a1n"
}

def _get_tofe_low_speed_io(name):
    return _tofe_io[_tofe_low_speed_io[name]]

_tofe_low_speed_pmod3_io = ["d9", "d8", "d11", "d10", "d13", "d12", "d15", "d14"]

def _get_tofe_low_speed_pmod3_io(n):
    return _get_tofe_low_speed_io(_tofe_low_speed_pmod3_io[n])

_io = [
    # clock / reset
    ("clk100", 0, Pins("AB13"), IOStandard("LVCMOS33")),
    ("cpu_reset", 0, Pins("Y3"), IOStandard("LVCMOS15"), Misc("PULLUP")),

    # serial
    ("serial", 0,
        Subsignal("tx", Pins(_get_tofe_low_speed_io("rx"))),
        Subsignal("rx", Pins(_get_tofe_low_speed_io("tx"))),
        IOStandard("LVCMOS33")
    ),

    # frontend switches / leds
    ("hdled", 0, Pins("J7"), IOStandard("LVCMOS15")),
    ("pwled", 0, Pins("H8"), IOStandard("LVCMOS15")), #pwled+ connected to 3.3V
    ("pwrsw", 0, Pins("F5"), IOStandard("LVCMOS15")),

    # user leds
    ("user_led", 0, Pins(_get_tofe_low_speed_io("led1")), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins(_get_tofe_low_speed_io("led2")), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins(_get_tofe_low_speed_io("led3")), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins(_get_tofe_low_speed_io("led4")), IOStandard("LVCMOS33")),

    # dram
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
    # ethernet
    ("eth_clocks", 0,
        Subsignal("tx", Pins("AB12")),
        Subsignal("rx", Pins("AA12")),
        IOStandard("LVCMOS33")
    ),
    ("eth", 0,
        Subsignal("rst_n", Pins("U8")),
        Subsignal("int_n", Pins("V9")),
        Subsignal("mdio", Pins("T8")),
        Subsignal("mdc", Pins("V7")),
        Subsignal("rx_ctl", Pins("U9")),
        Subsignal("rx_data", Pins("R9 R8 W6 Y6")),
        Subsignal("tx_ctl", Pins("W8")),
        Subsignal("tx_data", Pins("W9 Y8 AA6 AB6")),
        IOStandard("LVCMOS33")
    ),

    # serial
    ("serial_debug", 0,
        Subsignal("tx", Pins(_get_tofe_low_speed_pmod3_io(0))),
        Subsignal("rx", Pins(_get_tofe_low_speed_pmod3_io(1))),
        IOStandard("LVCMOS33")
    ),

    # hdmi in
    ("hdmi_in", 0,
        Subsignal("clk_p", Pins("L20"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("L22"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("M21"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("M22"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("N20"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("N22"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("P21"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("P22"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("T21"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("R22"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("R20"), IOStandard("LVCMOS33"))
    ),
    ("hdmi_in", 1,
        Subsignal("clk_p", Pins("M20"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("M19"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("J20"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("J22"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("H21"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("H22"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("K20"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("L19"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("L17"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("T18"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("V19"), IOStandard("LVCMOS33"))
    ),

    # hdmi out
    ("hdmi_out", 0,
        Subsignal("clk_p", Pins("Y11"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("AB11"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("W12"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("Y12"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("AA10"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("AB10"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("Y9"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("AB9"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("Y7"), IOStandard("I2C")),
        Subsignal("sda", Pins("Y10"), IOStandard("I2C")),
        Subsignal("hpd_notif", Pins("AB7"), IOStandard("LVCMOS33"))
    ),
    ("hdmi_out", 1,
        Subsignal("clk_p", Pins("T12"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("U12"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("Y15"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("AB15"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("AA16"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("AB16"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("U14"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("U13"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("Y17"), IOStandard("I2C")),
        Subsignal("sda", Pins("AB17"), IOStandard("I2C")),
        Subsignal("hpd_notif", Pins("AB18"), IOStandard("LVCMOS33"))
    ),
    ("fx2", 0,
        Subsignal("ifclk", Pins("P20"), IOStandard("LVCMOS33")),
        Subsignal("data", Pins("C20 C22 L15 K16 D21 D22 G19 F20 H18 H19 F21 F22 E20 E22 J19 H20"), IOStandard("LVCMOS33")),
        Subsignal("addr", Pins("B21 B22"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("flaga", Pins("N16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("flagb", Pins("P16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("flagc", Pins("R15"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("cs_n", Pins("J17"), IOStandard("LVCMOS33"),  Misc("DRIVE=12")),
        Subsignal("rd_n", Pins("P19"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("wr_n", Pins("R19"), IOStandard("LVCMOS33")),
        Subsignal("oe_n", Pins("H16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("pktend_n", Pins("J16"), IOStandard("LVCMOS33"),  Misc("DRIVE=12"))
    ),
]

class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.0

    def __init__(self):
        XilinxPlatform.__init__(self,  "xc6slx45t-fgg484-3", _io)
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
        self.add_platform_command("""CONFIG VCCAUX="3.3";""")

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        for i in range(2):
            try:
                self.add_period_constraint(self.lookup_request("hdmi_in", i).clk_p, 12)
            except ConstraintError:
                pass
        try:
            self.add_period_constraint(self.lookup_request("eth_clocks").rx, 8.0)
        except ConstraintError:
            pass

    def create_programmer(self):
        return iMPACT()
