from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer

_io = [
    ("clk50", 0, Pins("R2"), IOStandard("LVCMOS33")),

    ("user_led", 0, Pins("U2"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("M5")),
        Subsignal("rx", Pins("N6")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "U15 M17 N18 U16 R18 P18 T18 T17",
            "U17 N16 R16 N17 V17 R17"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("T15 M16 P15"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("L18"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("K17"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("P16"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("D9 B14 F14 C18"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "D11 B11 D8  C11 C8  B10 C9  A10 "
            "A15 A14 E13 B12 C13 A12 D13 A13 "
            "H18 G17 G16 F17 G14 E18 H16 H17 "
            "C17 D16 B17 E16 C16 E17 D15 D18 "
            ),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_p", Pins("B9 C14 G15 B16"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("A9 B15 F15 A17"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("P14"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("R15"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("K15"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("K18"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("V16"), IOStandard("LVCMOS15")),
        Subsignal("cs_n", Pins("J16"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),

    ("pcie_x1", 0,
        Subsignal("rst_n", Pins("N1"), IOStandard("LVCMOS33")),
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("rx_p", Pins("E4")),
        Subsignal("rx_n", Pins("E3")),
        Subsignal("tx_p", Pins("H2")),
        Subsignal("tx_n", Pins("H1"))
    ),
]


class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 20.0

    def __init__(self, toolchain="vivado", programmer="vivado"):
        XilinxPlatform.__init__(self, "xc7a50t-csg325-2", _io,
                                toolchain=toolchain)

        self.add_platform_command(
            "set_property CONFIG_VOLTAGE 1.5 [current_design]")
        self.add_platform_command(
            "set_property CFGBVS GND [current_design]")
        self.add_platform_command(
            "set_property BITSTREAM.CONFIG.CONFIGRATE 22 [current_design]")
        self.add_platform_command(
            "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 1 [current_design]")
        self.toolchain.bitstream_commands = [
            "set_property CONFIG_VOLTAGE 1.5 [current_design]",
            "set_property CFGBVS GND [current_design]",
            "set_property BITSTREAM.CONFIG.CONFIGRATE 22 [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 1 [current_design]",
        ]
        self.toolchain.additional_commands = \
            ["write_cfgmem -verbose -force -format bin -interface spix1 -size 64 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 35]")


    def create_programmer(self):
        if self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
