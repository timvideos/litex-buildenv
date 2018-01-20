# This file is Copyright (c) 2018 TimVideos
# License: BSD

from litex.build.generic_platform import *
from litex.build.openocd import OpenOCD
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [

    ("clk100", 0, Pins("F4"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("B18")),
        Subsignal("rx", Pins("A18")),
        IOStandard("LVCMOS33")),

    ("spiflash_4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("L13")),
        Subsignal("dq", Pins("K17", "K18", "L14", "M14")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash_1x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("L13")),
        Subsignal("mosi", Pins("K17")),
        Subsignal("miso", Pins("K18")),
        Subsignal("wp", Pins("L14")),
        Subsignal("hold", Pins("M14")),
        IOStandard("LVCMOS33")
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "M4 P4 M6 T1 L3 P5 M2 N1",
            "L4 N5 R2 K5 N6 K3"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("P2 P3 R1"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("N4"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("L1"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("N2"), IOStandard("SSTL15")),
        Subsignal("cs_n", Pins("K6"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("T6 U1"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "R7 V6 R8 U7 V7 R6 U6 R5",
            "T5 U3 V5 U4 V4 T4 V1 T3"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("U9 U2"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("V9 V2"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("L6"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("L5"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("M1"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("M3"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("U8"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),
]


class Platform(XilinxPlatform):
    name = "neso"
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
        XilinxPlatform.__init__(self, "xc7a100t-csg324-1", _io,
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
            return OpenOCD(config="board/numato_neso.cfg", flash_proxy_basename=proxy)
        elif self.programmer == "xc3sprog":
            return XC3SProg("saturn")
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))
