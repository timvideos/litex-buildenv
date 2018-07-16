from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [
    ("user_led", 0, Pins("K17"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("J17"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("L14"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("L15"), IOStandard("LVCMOS33")),
    ("user_led", 4, Pins("L16"), IOStandard("LVCMOS33")),
    ("user_led", 5, Pins("K16"), IOStandard("LVCMOS33")),
    ("user_led", 6, Pins("M15"), IOStandard("LVCMOS33")),
    ("user_led", 7, Pins("M16"), IOStandard("LVCMOS33")),

    ("user_sw", 0, Pins("B21"), IOStandard("LVCMOS33")),
    ("user_sw", 1, Pins("A21"), IOStandard("LVCMOS33")),
    ("user_sw", 2, Pins("E22"), IOStandard("LVCMOS33")),
    ("user_sw", 3, Pins("D22"), IOStandard("LVCMOS33")),
    ("user_sw", 4, Pins("E21"), IOStandard("LVCMOS33")),
    ("user_sw", 5, Pins("D21"), IOStandard("LVCMOS33")),
    ("user_sw", 6, Pins("G21"), IOStandard("LVCMOS33")),
    ("user_sw", 7, Pins("G22"), IOStandard("LVCMOS33")),


    ("user_btn", 0, Pins("P20"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("P19"), IOStandard("LVCMOS33")),
    ("user_btn", 2, Pins("P17"), IOStandard("LVCMOS33")),
    ("user_btn", 3, Pins("N17"), IOStandard("LVCMOS33")),


    ("clk100", 0, Pins("H4"), IOStandard("LVCMOS33")),

    ("cpu_reset", 0, Pins("M2"), IOStandard("LVCMOS33")),


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
        Subsignal("tx", Pins("Y21")),
        Subsignal("rx", Pins("Y22")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "U6 T5 Y6 T6 V2 T4 Y2 R2",
            "Y1 R4 W5 W1 AA6 U2"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("W6 U5 R6"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("V5"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("T1"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("R3"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("Y7 AA1"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "Y8  AB6  W9   AA8  AB7  V7  AB8  W7",
            "V4  AB2  AA5  AB3  AB5  W4  AB1  AA4"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("V9 Y3"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("V8 AA3"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("U3"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("V3"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("U1"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("W2"), IOStandard("SSTL15")),
        Subsignal("cs_n", Pins("T3"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("U7"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),

    ("eth_clocks", 0,
        Subsignal("tx", Pins("U20")),
        Subsignal("rx", Pins("W19")),
        IOStandard("LVCMOS33")
    ),
    ("eth", 0,
        Subsignal("rst_n", Pins("R14"), IOStandard("LVCMOS33")),
        Subsignal("int_n", Pins("V19")),
        Subsignal("mdio", Pins("P16")),
        Subsignal("mdc", Pins("R19")),
        Subsignal("rx_ctl", Pins("Y19")),
        Subsignal("rx_data", Pins("AB18 W20 W17 V20")),
        Subsignal("tx_ctl", Pins("T20")),
        Subsignal("tx_data", Pins("V18 U18 V17 U17")),
        IOStandard("LVCMOS33")
    ),

    ("hdmi_in", 0,
        Subsignal("clk_p", Pins("K4"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("J4"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("K1"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("J1"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("M1"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("L1"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("P2"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("N2"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("J2"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("H2"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("G2"), IOStandard("LVCMOS33")),
        Subsignal("cec", Pins("K2"), IOStandard("LVCMOS33")),  # FIXME
        # Subsignal("txen", Pins("R3"), IOStandard("LVCMOS33")),  # FIXME
    ),

    ("hdmi_out", 0,
        Subsignal("clk_p", Pins("L3"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("K3"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("B1"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("A1"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("E1"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("D1"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("G1"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("F1"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("D2"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("C2"), IOStandard("LVCMOS33")),
        Subsignal("cec", Pins("E2"), IOStandard("LVCMOS33")),  # FIXME
        Subsignal("hdp", Pins("B2"), IOStandard("LVCMOS33")), # FIXME
    ),
]

_connectors = []

_hdmi_infos = {
    "HDMI_OUT0_MNEMONIC": "OUT1",
    "HDMI_OUT0_DESCRIPTION" : (
      "  Add description\\r\\n"
    ),

    "HDMI_IN0_MNEMONIC": "IN1",
    "HDMI_IN0_DESCRIPTION" : (
      "  Add description\\r\\n"
    ),
}

class Platform(XilinxPlatform):
    name = "mimas_a7"
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
    spiflash_total_size = int((128/8)*1024*1024) # 256Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000
    spiflash_model = "n25q128"

    def __init__(self, toolchain="vivado", programmer="openocd"):
        XilinxPlatform.__init__(self, "xc7a50t-fgg484-1", _io, _connectors,
                                toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 34]")


    def create_programmer(self):
        if self.programmer == "openocd":
            proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
            return OpenOCD(config="board/numato_mimas_a7.cfg", flash_proxy_basename=proxy)
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
