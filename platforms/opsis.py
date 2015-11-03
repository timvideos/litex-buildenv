# Support for the Numato Opsis - The first HDMI2USB production board

from mibuild.generic_platform import *
from mibuild.xilinx import XilinxPlatform

from mibuild.openocd import OpenOCD
from mibuild.xilinx import UrJTAG
from mibuild.xilinx import iMPACT

_io = [
    ## FXO-HC536R - component U17
    # 100MHz - CMOS Crystal Oscillator
    #NET "clk"                  LOC =   "AB13"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/USRCLK)
    ("clk100", 0, Pins("AB13"), IOStandard("LVCMOS33")),

    ## FXO-HC536R - component U26
    # 27MHz - CMOS Crystal Oscillator
    #NET "clk"                  LOC =    "N19"       |IOSTANDARD =            None;     #                      (/SPI_Flash/27MHz)
    ("clk27", 0, Pins("N19"), IOStandard("LVCMOS33")),

    ## SW_PUSH - component SW1
    # Connected to Bank 3 - 1.5V bank
    #NET "???"                  LOC =     "Y3"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_0_3/SWITCH | Net-(R54-Pad2))
    ("cpu_reset", 0, Pins("Y3"), IOStandard("LVCMOS15"), Misc("PULLUP")),

    # CY7C68013A_100AC - component U2
    ("fx2", 0,
        #NET "fx2_ifclk"            LOC =    "P20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY-IFCLK)
        Subsignal("ifclk", Pins("P20"), IOStandard("LVCMOS33")),
        #NET "fx2_fd<0>"            LOC =    "C20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD0)
        #NET "fx2_fd<1>"            LOC =    "C22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD1)
        #NET "fx2_fd<2>"            LOC =    "L15"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD2)
        #NET "fx2_fd<3>"            LOC =    "K16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD3)
        #NET "fx2_fd<4>"            LOC =    "D21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD4)
        #NET "fx2_fd<5>"            LOC =    "D22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD5)
        #NET "fx2_fd<6>"            LOC =    "G19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD6)
        #NET "fx2_fd<7>"            LOC =    "F20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD7)
        #NET "fx2_fd<8>"            LOC =    "H18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD8)
        #NET "fx2_fd<9>"            LOC =    "H19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD9)
        #NET "fx2_fd<10>"           LOC =    "F21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD10)
        #NET "fx2_fd<11>"           LOC =    "F22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD11)
        #NET "fx2_fd<12>"           LOC =    "E20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD12)
        #NET "fx2_fd<13>"           LOC =    "E22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD13)
        #NET "fx2_fd<14>"           LOC =    "J19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD14)
        #NET "fx2_fd<15>"           LOC =    "H20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_FD15)
        Subsignal("data", Pins("C20 C22 L15 K16 D21 D22 G19 F20 H18 H19 F21 F22 E20 E22 J19 H20"), IOStandard("LVCMOS33")),
        #NET "fx2_fifoadr<0>"       LOC =    "B21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA4)
        #NET "fx2_fifoadr<1>"       LOC =    "B22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA5)
        Subsignal("addr", Pins("B21 B22"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        #NET "fx2_flaga"            LOC =    "N16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL0)
        #NET "fx2_flagb"            LOC =    "P16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL1)
        #NET "fx2_flagc"            LOC =    "R15"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL2)
        Subsignal("flaga", Pins("N16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("flagb", Pins("P16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        Subsignal("flagc", Pins("R15"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        #NET "fx2_flagd/slcs_n"     LOC =    "J17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA7)
        Subsignal("cs_n", Pins("J17"), IOStandard("LVCMOS33"),  Misc("DRIVE=12")),
        #NET "fx2_slrd"             LOC =    "P19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD0)
        Subsignal("rd_n", Pins("P19"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        #NET "fx2_slwr"             LOC =    "R19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD1)
        Subsignal("wr_n", Pins("R19"), IOStandard("LVCMOS33")),
        #NET "fx2_sloe"             LOC =    "H16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA2)
        Subsignal("oe_n", Pins("H16"), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
        #NET "fx2_pktend"           LOC =    "J16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA6)
        Subsignal("pktend_n", Pins("J16"), IOStandard("LVCMOS33"),  Misc("DRIVE=12")),

        #NET "fx2_ctl<3>"           LOC =    "M18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL3)
        #NET "fx2_ctl<4>"           LOC =    "M17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL4)
        #NET "fx2_ctl<5>"           LOC =    "R16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_CTL5)
        #NET "fx2_init5_n"          LOC =    "T19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_INT5)
        #NET "fx2_int<0>"           LOC =    "F18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA0)
        #NET "fx2_int<1>"           LOC =    "F19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA1)
        #NET "fx2_wu<2>"            LOC =    "H17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PA3)
        #NET "fx2_gpifadr<0>"       LOC =    "U20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC0)
        #NET "fx2_gpifadr<1>"       LOC =    "U22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC1)
        #NET "fx2_gpifadr<2>"       LOC =    "V21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC2)
        #NET "fx2_gpifadr<3>"       LOC =    "V22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC3)
        #NET "fx2_gpifadr<4>"       LOC =    "W20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC4)
        #NET "fx2_gpifadr<5>"       LOC =    "W22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC5)
        #NET "fx2_gpifadr<6>"       LOC =    "Y21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC6)
        #NET "fx2_gpifadr<7>"       LOC =    "Y22"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_PC7)
        #NET "fx2_gpifadr<8>"       LOC =   "AB21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Power/DONE | Net-(R28-Pad1))
        # Timers
        #NET "fx2_t<0>"             LOC =    "G17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/SPI_Flash/TDO-FPGA/TDO-JTAG | Net-(P3-Pad8) | Net-(R14-Pad1))
        ## \/ Strongly pulled (4k) to VCC3V3 via R56
        #NET "fx2_t<1>"             LOC =    "AB2"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Power/PROG_B | Net-(R15-Pad1))
        #NET "fx2_t<2>"             LOC =    "E18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/SPI_Flash/TDO-USB/TDI-FPGA | Net-(P3-Pad10) | Net-(R23-Pad1))
        #NET "fx2_rd_n"             LOC =    "K19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD)
        #NET "fx2_rdy<2>"           LOC =    "M16"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD2)
        #NET "fx2_rdy<3>"           LOC =    "N15"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD3)
        #NET "fx2_rdy<4>"           LOC =    "U19"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD4)
        #NET "fx2_rdy<5>"           LOC =    "T20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RD5)
        ## UART0
        #NET "fx2_rxd0"             LOC =    "P18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RXD1)
        #NET "fx2_txd0"             LOC =    "T17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_TXD1)
        ## UART1
        #NET "fx2_rxd1"             LOC =    "P17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_RXD0)
        #NET "fx2_txd1"             LOC =    "R17"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_TXD0)
        #
        #NET "fx2_t0"               LOC =    "G20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_T0)
        #NET "fx2_wr_n"             LOC =    "K18"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/CY_WR)
	# JTAG
        #  - TMS?
        #NET "fx2_rxd<0>"           LOC =    "D20"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Power/TMS | Net-(P3-Pad4) | Net-(R24-Pad1))
        #  - TCK
        #NET "fx2_rxd<1>"           LOC =    "A21"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Power/TCK | Net-(P3-Pad6) | Net-(R26-Pad1))
        ## \/ Strongly pulled (4k) to VCC3V3 via R52
        #NET "fx2_t<2>"             LOC =     "Y4"       |IOSTANDARD =        LVCMOS33 |SLEW=SLOW            |DRIVE=12            ;     #                      (/FPGA_Bank_1_2/INIT_B | Net-(R27-Pad1))

        ## Same pins as the EEPROM
        ## \/ Strongly pulled (2k) to VCC3V3 via R34
        #NET "fx2_scl"              LOC =     "G6"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SCL)
        #Subsignal("scl", Pins("G6"), IOStandard("I2C")),
        #NET "fx2_sda"              LOC =     "C1"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SDA)
        #Subsignal("sda", Pins("C1"), IOStandard("I2C")),
    ),

    ("i2c", 0,
        Subsignal("scl", Pins("G6"), IOStandard("LVCMOS15")),
        Subsignal("sda", Pins("C1"), IOStandard("LVCMOS15")),
    ),

    ## onBoard Quad-SPI Flash
    ## W25Q128FVEIG - component U3
    ## 128M (16M x 8) - 104MHz
    ("spiflash4x", 0,
        ## \/ Strongly pulled (10k) to VCC3V3 via R18
        #NET "???"                  LOC =    "AA3"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_CS_N)
        Subsignal("cs_n", Pins("AA3")),
        #NET "???"                  LOC =    "Y20"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_CLK)
        Subsignal("clk", Pins("Y20")),
        #NET "???"                  LOC =   "AB20"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_MOSI_CSI_N_MISO0)
        ## \/ Strongly pulled (10k) to VCC3V3 via R19
        #NET "???"                  LOC =   "AA20"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_DO_DIN_MISO1 | Net-(R16-Pad1))
        ## \/ Strongly pulled (10k) to VCC3V3 via R20
        #NET "???"                  LOC =    "R13"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_D1_MISO2 | Net-(R17-Pad1))
        ## \/ Strongly pulled (10k) to VCC3V3 via R21
        #NET "???"                  LOC =    "T14"       |IOSTANDARD =            None;     #                      (/FPGA_Bank_1_2/SPI_D2_MISO3)
        Subsignal("dq", Pins("AB20", "AA20", "R13", "T14")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")
    ),

    ## onBoard Leds
    # NET "Led<0>" LOC = "U18"; # Bank = 1, Pin name = IO_L52N_M1DQ15,       Sch name = LD0
    #("user_led", 0, Pins("U18")),

    ## TEMAC Ethernet MAC - FIXME
    # 10/100/1000 Ethernet PHY
    ## RTL8211E-VL - component U20 - RGMII
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

	## 24AA02E48 - component U23
    ## 2 Kbit Electrically Erasable PROM
    ## Pre-programmed Globally Unique, 48-bit Node Address
    ## The device is organized as two blocks of 128 x 8-bit memory with a 2-wire serial interface.
    ##
    ## \/ Strongly pulled (2k) to VCC3V3 via R34
    #NET "eeprom_scl"           LOC =     "G6"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SCL)
    #NET "eeprom_sda"           LOC =     "C1"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SDA)

    ## DDR3
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

    ## onboard HDMI IN1
    ## HDMI - connector J5 - Direction RX
    ("hdmi_in", 0,
        Subsignal("clk_p", Pins("L20")),
        Subsignal("clk_n", Pins("L22")),
        Subsignal("data0_p", Pins("M21")),
        Subsignal("data0_n", Pins("M22")),
        Subsignal("data1_p", Pins("N20")),
        Subsignal("data1_n", Pins("N22")),
        Subsignal("data2_p", Pins("P21")),
        Subsignal("data2_n", Pins("P22")),
        Subsignal("scl", Pins("T21"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("R22"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("R20"), IOStandard("LVCMOS33"))
    ),

    ## onboard HDMI IN2
    ## HDMI - connector J4 - Direction RX
    ("hdmi_in", 1,
        Subsignal("clk_p", Pins("M20")),
        Subsignal("clk_n", Pins("M19")),
        Subsignal("data0_p", Pins("J20")),
        Subsignal("data0_n", Pins("J22")),
        Subsignal("data1_p", Pins("H21")),
        Subsignal("data1_n", Pins("H22")),
        Subsignal("data2_p", Pins("K20")),
        Subsignal("data2_n", Pins("L19")),
        Subsignal("scl", Pins("L17"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("T18"), IOStandard("LVCMOS33")),
        Subsignal("hpd_en", Pins("V19"), IOStandard("LVCMOS33"))
    ),

    # Debug header?
    #("debug", 0, Pins("AA2"), IOStandard("LVCMOS15")), # (/FPGA_Bank_0_3/DEBUG_IO0)

    ## UARTs
    # To Cypress FX2 UART0
    # WARNING: This was labelled incorrectly - https://github.com/timvideos/HDMI2USB-numato-opsis-hardware/issues/13
    # Current use FX2 firmware from https://github.com/mithro/fx2lib/tree/cdc-usb-serialno-from-eeprom/examples/cdc/to-uart
    # FIXME: Will be supported by opsis-mode-switch --mode=serial soon.
    # FIXME: Will be supported by opsis-mode-siwtch --mode=jtag longer term.
    ("serial", 0,
        # CY_RXD1 - P18 - Cypress RXD0
        Subsignal("tx", Pins("P18"), IOStandard("LVCMOS33")),
        # CY_TXD1 - T17 - Cypress TXD0
        Subsignal("rx", Pins("T17"), IOStandard("LVCMOS33")),
    ),
    # To Cypress FX2 UART1
    #("serial", 1,
    #    Subsignal("rx", Pins("A16"), IOStandard("LVCMOS33")),
    #    Subsignal("tx", Pins("B16"), IOStandard("LVCMOS33")),
    #),
    #
    # Florent's UART (requires desoldering 2 resistors on the SD card connector)
    #("serial", 0,
    #    # SD_CMD
    #    Subsignal("tx", Pins("U6"), IOStandard("LVCMOS33")),
    #    # SD_DAT0
    #    Subsignal("rx", Pins("AA4"), IOStandard("LVCMOS33")),
    #),

    ## onboard HDMI OUT

    ## HDMI - connector J3 - Direction TX
    ("hdmi_out", 0,
        Subsignal("clk_p", Pins("Y11"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("AB11"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("W12"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("Y12"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("AA10"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("AB10"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("Y9"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("AB9"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("Y7"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("Y10"), IOStandard("LVCMOS33")),
        Subsignal("hpd_notif", Pins("AB7"), IOStandard("LVCMOS33"))
    ),

    ## HDMI - connector J2 - Direction TX
    ("hdmi_out", 1,
        Subsignal("clk_p", Pins("T12"), IOStandard("TMDS_33")),
        Subsignal("clk_n", Pins("U12"), IOStandard("TMDS_33")),
        Subsignal("data0_p", Pins("Y15"), IOStandard("TMDS_33")),
        Subsignal("data0_n", Pins("AB15"), IOStandard("TMDS_33")),
        Subsignal("data1_p", Pins("AA16"), IOStandard("TMDS_33")),
        Subsignal("data1_n", Pins("AB16"), IOStandard("TMDS_33")),
        Subsignal("data2_p", Pins("U14"), IOStandard("TMDS_33")),
        Subsignal("data2_n", Pins("U13"), IOStandard("TMDS_33")),
        Subsignal("scl", Pins("Y17"), IOStandard("LVCMOS33")),
        Subsignal("sda", Pins("AB17"), IOStandard("LVCMOS33")),
        Subsignal("hpd_notif", Pins("AB18"), IOStandard("LVCMOS33"))
    ),


#        ("fpga_cfg",
#            Subsignal("din", Pins("T14")),
#            Subsignal("cclk", Pins("R14")),
#            Subsignal("init_b", Pins("T12")),
#            Subsignal("prog_b", Pins("A2")),
#            Subsignal("done", Pins("T15")),
#        ),
#        ("jtag",
#            Subsignal("tms", Pins("B2")),
#            Subsignal("tdo", Pins("B16")),
#            Subsignal("tdi", Pins("B1")),
#            Subsignal("tck", Pins("A15")),
#        ),

]

_connectors = [
]

_hdmi_infos = {
    "HDMI_IN0_MNEMONIC": "J5",
    "HDMI_IN0_DESCRIPTION" : "XXX",

    "HDMI_IN1_MNEMONIC": "J4",
    "HDMI_IN1_DESCRIPTION" : "XXX",

    "HDMI_OUT0_MNEMONIC": "J3",
    "HDMI_OUT0_DESCRIPTION" : "XXX",

    "HDMI_OUT1_MNEMONIC": "J2",
    "HDMI_OUT1_DESCRIPTION" : "XXX"
}

class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.0
    hdmi_infos = _hdmi_infos

    def __init__(self, programmer="openocd"):
        # XC6SLX45T-3FGG484C
        XilinxPlatform.__init__(self,  "xc6slx45t-fgg484-3", _io, _connectors)

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

        self.programmer = programmer

        # FPGA AUX is connected to the 3.3V supply
        self.add_platform_command("""CONFIG VCCAUX="3.3";""")

    def create_programmer(self):
	# Preferred programmer - Needs ixo-usb-jtag and latest openocd.
        if self.programmer == "openocd":
            return OpenOCD(config="board/numato_opsis.cfg")
	# Alternative programmers - not regularly tested.
        elif self.programmer == "urjtag":
            return UrJTAG(cable="USBBlaster")
        elif self.programmer == "impact":
            return iMPACT()
        else:
            raise ValueError("{} programmer is not supported".format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        for i in range(2):
            try:
                self.add_period_constraint(self.lookup_request("hdmi_in", i).clk_p, 12)
            except ConstraintError:
                pass

        try:
            self.add_period_constraint(self.lookup_request("eth_clocks").rx, 40.0)
        except ConstraintError:
            pass

        try:
            self.add_period_constraint(self.lookup_request("fx2").ifclk, 20.8)
        except ConstraintError:
            pass


