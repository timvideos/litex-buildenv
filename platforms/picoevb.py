from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer

_io = [
    # SYS clock 100 MHz (input) signal. The sys_clk_p and sys_clk_n
    # signals are the PCI Express reference clock.
    #set_property PACKAGE_PIN B6 [get_ports sys_clk_p]
    ("clk100", 0, Pins("B6"), IOStandard("LVCMOS33")),

    #set_property PACKAGE_PIN V14 [get_ports {status_leds[3]}]
    #set_property PACKAGE_PIN V13 [get_ports {status_leds[2]}]
    #set_property PACKAGE_PIN V11 [get_ports {status_leds[1]}]
    #set_property PACKAGE_PIN V12 [get_ports {status_leds[0]}]
    #set_property IOSTANDARD LVCMOS33 [get_ports {status_leds[3]}]
    #set_property IOSTANDARD LVCMOS33 [get_ports {status_leds[2]}]
    #set_property IOSTANDARD LVCMOS33 [get_ports {status_leds[1]}]
    #set_property IOSTANDARD LVCMOS33 [get_ports {status_leds[0]}]
    #set_property PULLUP true [get_ports {status_leds[3]}]
    #set_property PULLUP true [get_ports {status_leds[2]}]
    #set_property PULLUP true [get_ports {status_leds[1]}]
    #set_property PULLUP true [get_ports {status_leds[0]}]
    #set_property DRIVE 8 [get_ports {status_leds[3]}]
    #set_property DRIVE 8 [get_ports {status_leds[2]}]
    #set_property DRIVE 8 [get_ports {status_leds[1]}]
    #set_property DRIVE 8 [get_ports {status_leds[0]}]
    ("user_led", 0, Pins("V12"), IOStandard("LVCMOS33"), Drive(8), Misc("PULLUP")),
    ("user_led", 1, Pins("V11"), IOStandard("LVCMOS33"), Drive(8), Misc("PULLUP")),
    ("user_led", 2, Pins("V13"), IOStandard("LVCMOS33"), Drive(8), Misc("PULLUP")),
    ("user_led", 3, Pins("V14"), IOStandard("LVCMOS33"), Drive(8), Misc("PULLUP")),

    ## Serial input/output
    ## Available on NanoEVB only!
    #set_property IOSTANDARD LVCMOS33 [get_ports RxD]
    #set_property IOSTANDARD LVCMOS33 [get_ports TxD]
    #set_property PACKAGE_PIN V17 [get_ports RxD]
    #set_property PACKAGE_PIN V16 [get_ports TxD]
    #set_property PULLUP true [get_ports RxD]
    #set_property OFFCHIP_TERM NONE [get_ports TxD]
    ("serial", 0,
        Subsignal("tx", Pins("V16")), # MCU_RX
        Subsignal("rx", Pins("V17")), # MCU_TX
        IOStandard("LVCMOS33"),
    ),

    ## SYS reset (input) signal.  The sys_reset_n signal is generated
    ## by the PCI Express interface (PERST#).
    #set_property PACKAGE_PIN A10 [get_ports sys_rst_n]
    #set_property IOSTANDARD LVCMOS33 [get_ports sys_rst_n]
    #set_property PULLDOWN true [get_ports sys_rst_n]

    ## PCIe x1 link
    #set_property PACKAGE_PIN G4 [get_ports pcie_mgt_rxp]
    #set_property PACKAGE_PIN G3 [get_ports pcie_mgt_rxn]
    #set_property PACKAGE_PIN B2 [get_ports pcie_mgt_txp]
    #set_property PACKAGE_PIN B1 [get_ports pcie_mgt_txn]
    ("pcie_x1", 0,
        Subsignal("rst_n", Pins("A10"), IOStandard("LVCMOS33"), Misc("PULLDOWN")),
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("rx_p", Pins("G4")),
        Subsignal("rx_n", Pins("G3")),
        Subsignal("tx_p", Pins("B2")),
        Subsignal("tx_n", Pins("B1"))
    ),

    ## clkreq_l is active low clock request for M.2 card to
    ## request PCI Express reference clock
    #set_property PACKAGE_PIN A9 [get_ports clkreq_l]
    #set_property IOSTANDARD LVCMOS33 [get_ports clkreq_l]
    #set_property PULLDOWN true [get_ports clkreq_l]

    ## High-speed configuration so FPGA is up in time to negotiate with PCIe root complex
    #set_property BITSTREAM.CONFIG.CONFIGRATE 33 [current_design]
    #set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]
    #set_property CONFIG_MODE SPIx4 [current_design]
    #set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES [current_design]
    #set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
]


class Platform(XilinxPlatform):
    name = "picoevb"
    default_clk_name = "clk100"
    default_clk_period = 10.0

    # From https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf
    # 17536096 bits == 2192012 == 0x21728c -- Therefore 0x220000
    gateware_size = 0x220000

    # ???
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((256/8)*1024*1024) # 256Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000
    spiflash_model = "n25q128"

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

        self.add_platform_command("""
create_clock -name pcie_phy_clk -period 10.0 [get_pins {{pcie_phy/pcie_support_i/pcie_i/inst/inst/gt_top_i/pipe_wrapper_i/pipe_lane[0].gt_wrapper_i/gtp_channel.gtpe2_channel_i/TXOUTCLK}}]
""")

    def create_programmer(self):
        if self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
