# Numato Elbert v2
# https://numato.com/product/elbert-v2-spartan-3a-fpga-development-board
# https://numato.com/docs/elbert-v2-spartan-3a-fpga-development-board/
# https://productdata.numato.com/assets/downloads/fpga/elbertv2/elbertv2.ucf
#
# Xilinx Spartan 3A FPGA (50k gates)
# https://www.xilinx.com/support/documentation/user_guides/ug332.pdf
#
# Digilent Pmod USBUART
# https://store.digilentinc.com/pmod-usbuart-usb-to-uart-interface/
#
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform


_io = [
    ("clk12", 0, Pins("P129"), IOStandard("LVCMOS33")),

    # XXX: Elbert v2 does not have any dedicated UART pins assigned!
    # XXX: As work around assume using Digilent Pmod USBUART on PMOD port P4
    # XXX: (which is the PMOD nearest the power/programming USB connector)
    # XXX: Pmod USBUART should be plugged into top row of P4
    #
    # Digilent Pmod USBUART connection:
    # 1 - RTS -> P141
    # 2 - RXD -> P138
    # 3 - TXD -> P134
    # 4 - CTS -> P130
    # 5 - GND
    # 6 - VCC
    #  J2
    # 
    # NOTE: this differs from pin assignment used by elbertV2UartDemo
    #       with http://numato.com/ft232rl-breakout-module/, due to
    #       different ordering of pins.
    #
    ("serial", 0,
        Subsignal("tx", Pins("P134"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),
        Subsignal("rx", Pins("P138"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW"))),

    # Elbert v2 SPI Flash connection not in Numato User Constraints File; 
    # pin numbers determined from schematics
    #
    # Bank 2 Pin 41 - CS
    # Bank 2 Pin 72 - SCK
    # Bank 2 Pin 62 - SI
    # Bank 2 Pin 71 - SO
    #
    ("spiflash", 0,
        Subsignal("cs_n", Pins("P41")),
        Subsignal("clk", Pins("P72")),
        Subsignal("mosi", Pins("P62")),
        Subsignal("miso", Pins("P71"), Misc("PULLUP")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")),

    # Elbert v2 does not have external DDRAM / Clock -- omitted

    # Small DIP switches
    # DP1 (user_sw:0) -> DP8 (user_sw:7)
    ("user_sw", 0, Pins("P70"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 1, Pins("P69"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 2, Pins("P68"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 3, Pins("P64"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 4, Pins("P63"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 5, Pins("P60"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 6, Pins("P59"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_sw", 7, Pins("P58"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    # Despite being marked as "sw" these are actually buttons which need
    # debouncing.
    # sw1 (user_btn:0) through sw6 (user_btn:5)
    ("user_btn", 0, Pins("P80"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 1, Pins("P79"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 2, Pins("P78"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 3, Pins("P77"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("user_btn", 4, Pins("P76"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    # Use SW6 as the reset button for now.
    ("user_btn", 5, Pins("P75"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    # LEDs 1 through 8
    ("user_led", 0, Pins("P46"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 1, Pins("P47"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 2, Pins("P48"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 3, Pins("P49"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 4, Pins("P50"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 5, Pins("P51"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 6, Pins("P54"), IOStandard("LVCMOS33"), Drive(12)),
    ("user_led", 7, Pins("P55"), IOStandard("LVCMOS33"), Drive(12)),

    ("mmc", 0,
        Subsignal("dat", Pins("P83 P82 P90 P85"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),       # 4 bits, LSB first

        Subsignal("cmd", Pins("P84"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),

        Subsignal("clk", Pins("P57"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW"))),

    ("sevenseg", 0,
        Subsignal("segment7", Pins("P117"), IOStandard("LVCMOS33")),  # A
        Subsignal("segment6", Pins("P116"), IOStandard("LVCMOS33")),  # B
        Subsignal("segment5", Pins("P115"), IOStandard("LVCMOS33")),  # C
        Subsignal("segment4", Pins("P113"), IOStandard("LVCMOS33")),  # D
        Subsignal("segment3", Pins("P112"), IOStandard("LVCMOS33")),  # E
        Subsignal("segment2", Pins("P111"), IOStandard("LVCMOS33")),  # F
        Subsignal("segment1", Pins("P110"), IOStandard("LVCMOS33")),  # G
        Subsignal("segment0", Pins("P114"), IOStandard("LVCMOS33")),  # Dot
        Subsignal("enable2",  Pins("P124"), IOStandard("LVCMOS33"))), # EN2
        Subsignal("enable1",  Pins("P121"), IOStandard("LVCMOS33")),  # EN1
        Subsignal("enable0",  Pins("P120"), IOStandard("LVCMOS33")),  # EN0


    ("audio", 0,
        Subsignal("channel1", Pins("P88"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),      # AUDIO_L
        Subsignal("channel2", Pins("P87"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW"))),     # AUDIO_R

    ("vga_out", 0,
        Subsignal("hsync_n", Pins("P93"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),
        Subsignal("vsync_n", Pins("P92"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),
        Subsignal("r", Pins("P103 P104 P105"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),      # Red   -- 3 bits, LSB first
        Subsignal("g", Pins("P99 P101 P102"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")),      # Green -- 3 bits, LSB first
        Subsignal("b", Pins("P96 P98"), IOStandard("LVCMOS33"),
                  Misc("SLEW=SLOW")))      # Blue  -- 2 bits, LSB first
]

_connectors = [
    ("P1", "P31 P32 P28 P30 P27 P29 P24 P25"),         # Pins 1-8, LSB first
    ("P6", "P19 P21 P18 P20 P15 P16 P12 P13"),         # Pins 1-8, LSB first
    ("P2", "P10 P11 P7 P8 P3 P5 P4 P6"),               # Pins 1-8, LSB first
    ("P4", "P141 P143 P138 P139 P134 P135 P130 P132"), # Pins 1-8, LSB first

    # XXX: Two input PINs of P5 Header IO_P5[1] and IO_P5[7] should have pullups
    # XXX: Unclear how to specify that here
    ("P5", "P125 P123 P127 P126 P131 P91 P142 P140"),  # Pins 1-8, LSB first
]


class Platform(XilinxPlatform):
    name = "elbertv2"
    default_clk_name = "clk12"  # 12 MHz
    default_clk_period = 83.333 # ns

    # The ElbertV2 has a XC3S50A: bitstream takes up 54,664 bytes (437,312 bits)
    # 0x10000 offset (512Kbit) gives plenty of space
    gateware_size = 0x10000

    # M25P16 - component U1
    # 16Mb - 75 MHz clock frequency
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    #	/*             name,  erase_cmd, chip_erase_cmd, device_id, pagesize, sectorsize, size_in_bytes */
    #	FLASH_ID("st m25p16",      0xd8,           0xc7, 0x00152020,   0x100,    0x10000,      0x200000),
    spiflash_model = "m25p16"
    spiflash_read_dummy_bits = 8
    spiflash_clock_div = 4
    spiflash_total_size = int((16/8)*1024*1024) # 16Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    def __init__(self):
        XilinxPlatform.__init__(self, "xc3s50a-4tq144", _io, _connectors)

    def create_programmer(self):
        raise NotImplementedError
