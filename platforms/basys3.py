# This file is Copyright (c) 2015 Yann Sionneau <yann@sionneau.net>
# This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

from litex.build.generic_platform import *
from litex.build.openocd import OpenOCD
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [
    ("user_led", 0, Pins("U16"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("E19"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("U19"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("V19"), IOStandard("LVCMOS33")),
    ("user_led", 4, Pins("W18"), IOStandard("LVCMOS33")),
    ("user_led", 5, Pins("U15"), IOStandard("LVCMOS33")),
    ("user_led", 6, Pins("U14"), IOStandard("LVCMOS33")),
    ("user_led", 7, Pins("V14"), IOStandard("LVCMOS33")),
    ("user_led", 8, Pins("V13"), IOStandard("LVCMOS33")),
    ("user_led", 9, Pins("V3"), IOStandard("LVCMOS33")),
    ("user_led", 10, Pins("W3"), IOStandard("LVCMOS33")),
    ("user_led", 11, Pins("U3"), IOStandard("LVCMOS33")),
    ("user_led", 12, Pins("P3"), IOStandard("LVCMOS33")),
    ("user_led", 13, Pins("N3"), IOStandard("LVCMOS33")),
    ("user_led", 14, Pins("P1"), IOStandard("LVCMOS33")),
    ("user_led", 15, Pins("L1"), IOStandard("LVCMOS33")),

    ("user_sw", 0, Pins("V17"), IOStandard("LVCMOS33")),
    ("user_sw", 1, Pins("V16"), IOStandard("LVCMOS33")),
    ("user_sw", 2, Pins("W16"), IOStandard("LVCMOS33")),
    ("user_sw", 3, Pins("W17"), IOStandard("LVCMOS33")),
    ("user_sw", 4, Pins("W15"), IOStandard("LVCMOS33")),
    ("user_sw", 5, Pins("V15"), IOStandard("LVCMOS33")),
    ("user_sw", 6, Pins("W14"), IOStandard("LVCMOS33")),
    ("user_sw", 7, Pins("W13"), IOStandard("LVCMOS33")),
    ("user_sw", 8, Pins("V2"), IOStandard("LVCMOS33")),
    ("user_sw", 9, Pins("T3"), IOStandard("LVCMOS33")),
    ("user_sw", 10, Pins("T2"), IOStandard("LVCMOS33")),
    ("user_sw", 11, Pins("R3"), IOStandard("LVCMOS33")),
    ("user_sw", 12, Pins("W2"), IOStandard("LVCMOS33")),
    ("user_sw", 13, Pins("U1"), IOStandard("LVCMOS33")),
    ("user_sw", 14, Pins("T1"), IOStandard("LVCMOS33")),
    ("user_sw", 15, Pins("R2"), IOStandard("LVCMOS33")),

    ("user_btn", 0, Pins("W19"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("T17"), IOStandard("LVCMOS33")),
    ("user_btn", 2, Pins("T18"), IOStandard("LVCMOS33")),
    ("user_btn", 3, Pins("U17"), IOStandard("LVCMOS33")),
    ("user_btn", 4, Pins("U18"), IOStandard("LVCMOS33")),

    ("clk100", 0, Pins("W5"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("A18")),
        Subsignal("rx", Pins("B18")),
        IOStandard("LVCMOS33")),

    ("spiflash_4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("K19")),
        Subsignal("dq", Pins("D18", "D19", "G18", "F18")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash_1x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("K19")),
        Subsignal("mosi", Pins("D18")),
        Subsignal("miso", Pins("D19")),
        Subsignal("wp", Pins("G18")),
        Subsignal("hold", Pins("F18")),
        IOStandard("LVCMOS33")
    ),
]


class Platform(XilinxPlatform):
    name = "basys3"
    default_clk_name = "clk100"
    default_clk_period = 10.0

    # From https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf
    # 17536096 bits == 2192012 == 0x21728c -- Therefore 0x220000
    gateware_size = 0x220000

    # Micron N25Q128A13ESF40 (ID 0x0018ba20)
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_model = "n25q128a13"
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((128/8)*1024*1024) # 128Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    def __init__(self, toolchain="vivado", programmer="openocd"):
        XilinxPlatform.__init__(self, "xc7a35t-cpg236-1", _io,
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
            return OpenOCD(config="board/digilent_arty.cfg", flash_proxy_basename=proxy)
        elif self.programmer == "xc3sprog":
            return XC3SProg("nexys4")
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))
