from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer

_io = [
    # U11F
    ("clk50", 0, Pins("R2"), IOStandard("LVCMOS33")),

    ("user_led", 0, Pins("U2"), IOStandard("LVCMOS33")),


    ("serial", 0,
        #set_property PACKAGE_PIN M5 [get_ports {MCU_RX}]
        Subsignal("tx", Pins("M5")),
        #set_property PACKAGE_PIN N6 [get_ports {MCU_TX}]
        Subsignal("rx", Pins("N6")),
        IOStandard("LVCMOS33"),
    ),

    # ./basic_overlay.srcs/sources_1/bd/overlay1/ip/overlay1_mig_7series_0_0/overlay1_mig_7series_0_0/user_design/constraints/overlay1_mig_7series_0_0.xdc
    ("ddram", 0,
        Subsignal("a", Pins(
            "U15 M17 N18 U16 R18 P18 T18 T17",
            "U17 N16 R16 N17 V17 R17"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("T15 M16 P15"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("L18"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("K17"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("P16"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("D9 B14"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "D11 B11 D8 C11 C8 B10 C9 A10",
            "A15 A14 E13 B12 C13 A12 D13 A13"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_p", Pins("B9 C14"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("A9 B15"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("P14"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("R15"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("K15"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("K18"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("V16"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),

    # ./basic_overlay.srcs/constrs_1/imports/netvcr/netvcr-evt1.xdc
    ("pcie_x1", 0,
        Subsignal("rst_n", Pins("N1"), IOStandard("LVCMOS33")),
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("rx_p", Pins("E4")),
        Subsignal("rx_n", Pins("E3")),
        Subsignal("tx_p", Pins("H2")),
        Subsignal("tx_n", Pins("H1"))
    ),

    ("hdmi_in", 0,
        #set_property PACKAGE_PIN P4 [get_ports HDMI_RX_CLK_P]
        #set_property PACKAGE_PIN P3 [get_ports HDMI_RX_CLK_N]
        Subsignal("clk_p", Pins("P4"), IOStandard("TDMS_33")),
        Subsignal("clk_n", Pins("P3"), IOStandard("TDMS_33")),
        #set_property PACKAGE_PIN U4 [get_ports HDMI_RX_0_P]
        #set_property PACKAGE_PIN V4 [get_ports HDMI_RX_0_N]
        Subsignal("data0_p", Pins("U4"), IOStandard("TDMS_33")),
        Subsignal("data0_n", Pins("V4"), IOStandard("TDMS_33")),
        #set_property PACKAGE_PIN P6 [get_ports HDMI_RX_1_P]
        #set_property PACKAGE_PIN P5 [get_ports HDMI_RX_1_N]
        Subsignal("data1_p", Pins("P6"), IOStandard("TDMS_33")),
        Subsignal("data1_n", Pins("P5"), IOStandard("TDMS_33")),
        #set_property PACKAGE_PIN R7 [get_ports HDMI_RX_2_P]
        #set_property PACKAGE_PIN T7 [get_ports HDMI_RX_2_N]
        Subsignal("data2_p", Pins("R7"), IOStandard("TDMS_33")),
        Subsignal("data2_n", Pins("T7"), IOStandard("TDMS_33")),
        # --
        #Subsignal("scl", Pins("Y4"), IOStandard("LVCMOS33")),
        #Subsignal("sda", Pins("AB5"), IOStandard("LVCMOS33")),
        #Subsignal("cec", Pins("AA5"), IOStandard("LVCMOS33")),  # FIXME
        #Subsignal("txen", Pins("R3"), IOStandard("LVCMOS33")),  # FIXME
        #Subsignal("hpa", Pins("AB12"), IOStandard("LVCMOS33")), # FIXME
    ),

    ("hdmi_out", 0,
        # set_property PACKAGE_PIN R3 [get_ports {HDMI_TX_CLK_P[0]}]
        # set_property PACKAGE_PIN T2 [get_ports {HDMI_TX_CLK_N[0]}]
        Subsignal("clk_p", Pins("R3"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("T2"), IOStandard("TMDS_33")),
        # set_property PACKAGE_PIN T4 [get_ports {HDMI_TX_0_P[0]}]
        # set_property PACKAGE_PIN T3 [get_ports {HDMI_TX_0_N[0]}]
        Subsignal("data0_p", Pins("T4"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("T3"), IOStandard("TMDS_33")),
        # set_property PACKAGE_PIN U6 [get_ports {HDMI_TX_1_P[0]}]
        # set_property PACKAGE_PIN U5 [get_ports {HDMI_TX_1_N[0]}]
        Subsignal("data1_p", Pins("U6"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("U5"), IOStandard("TMDS_33")),
        # set_property PACKAGE_PIN U7 [get_ports {HDMI_TX_2_P[0]}]
        # set_property PACKAGE_PIN V6 [get_ports {HDMI_TX_2_N[0]}]
        Subsignal("data2_p", Pins("V7"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("V6"), IOStandard("TMDS_33")),
        # --

        # LV_CEC - R5
        # LV_HPD - T5

        # LV_SCL - V3 - # Don't drive LV_SCL
        # LV_SDA - V2 - # Don't drive LV_SDA

        # HPD_OVER      - V8
        # SDA_OVER_UP   - V7
        # SDA_OVER_DN   - R6

        #Subsignal("scl", Pins("U3"), IOStandard("LVCMOS33")),
        #Subsignal("sda", Pins("V3"), IOStandard("LVCMOS33")),
        #Subsignal("cec", Pins("AA4"), IOStandard("LVCMOS33")),  # FIXME
        #Subsignal("hdp", Pins("AB13"), IOStandard("LVCMOS25")), # FIXME
    ),
]


class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 20.0

    def __init__(self, toolchain="vivado", programmer="vivado"):
        XilinxPlatform.__init__(self, "xc7a50t-csg325-2", _io,
                                toolchain=toolchain)
#        self.toolchain.bitstream_commands = \
#            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 1 [current_design]"]
        self.add_platform_command(
            "set_property BITSTREAM.CONFIG.CONFIGRATE 22 [current_design]")
        self.add_platform_command(
            "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 1 [current_design]")
            
#        self.toolchain.additional_commands = \
#            ["write_cfgmem -force -format bin -interface spix1 -size 16 "
#             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
#        self.toolchain.additional_commands = \
#            ["write_cfgmem -force -format bin -interface spix1 -size 32 "
#             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -verbose -force -format bin -interface spi1 -size 64 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 35]")


    def create_programmer(self):
        if self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q64-1.8v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
