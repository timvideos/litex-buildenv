# Support for the Numato Galatea - PCI Express Spartan 6 Development Board
# https://numato.com/product/galatea-pci-express-spartan-6-fpga-development-board

from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, iMPACT


_io = [
    # Clock U18 - 100MHz - CMOS Crystal Oscillator
    #NET "CLK1"               LOC = "G9"     | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;                                  # Bank = 0
    ("clk100", 0, Pins("AB13"), IOStandard("LVCMOS33")),
    # Clock U19 - 100MHz - CMOS Crystal Oscillator
    #NET "CLK2"               LOC = "Y13"    | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;                                  # Bank = 2
    ("clk2", 0, Pins("AB13"), IOStandard("LVCMOS33")),
    # Clock U17 - 100MHz - CMOS Crystal Oscillator
    #NET "CLK3"               LOC = "AB13"   | IOSTANDARD = "LVCMOS33" | Period = 100 MHz;                                  # Bank = 2
    ("clk3", 0, Pins("AB13"), IOStandard("LVCMOS33")),

    # Clock U21 SMA Clock
    #NET "EXT_CLK1"           LOC = "U12"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2

    # Clock U6 SMA Clock
    #NET "EXT_CLK2"           LOC = "T12"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2

    # SW1 Switch

    ## SW_PUSH - component SW1
    # Connected to Bank 3 - 1.5V bank
    #NET "RST_N"              LOC = "AB19"   | IOSTANDARD = "LVCMOS33" | PULLUP ;                                           # Bank = 2
    ("cpu_reset", 0, Pins("AB19"), IOStandard("LVCMOS15"), Misc("PULLUP")),

    ########################################################################################################################################################
    #                                                             UART                                                                                     #
    ########################################################################################################################################################

    #NET "UART_TX"            LOC = "V17"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
    #NET "UART_RX"            LOC = "W18"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2

    ########################################################################################################################################################
    #                                                             SPI Flash                                                                                #
    ########################################################################################################################################################

    #NET "SPI_Flash_SCK"      LOC = "Y20"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
    #NET "SPI_Flash_MISO"     LOC = "T14"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
    #NET "SPI_Flash_MOSI"     LOC = "AB20"   | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
    #NET "SPI_Flash_SS"       LOC = "AA3"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2

    ## onBoard Quad-SPI Flash
    ## N25Q128A13ESE40E - 128 Mb QSPI flash memory

    #QSPI_FLASH_SCLK		Y20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO0		AB20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO1		AA20	LVCMOS33	16	FAST
    #QSPI_FLASH_IO2		R13	LVCMOS33	16	FAST
    #QSPI_FLASH_IO3		T14	LVCMOS33	16	FAST
    #QSPI_FLASH_SS		AA3	LVCMOS33	16	FAST


    ("spiflash1x", 0,
        #NET "SPI_Flash_SCK"      LOC = "Y20"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
        Subsignal("clk", Pins("Y20")),
        #NET "SPI_Flash_SS"       LOC = "AA3"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
        Subsignal("cs_n", Pins("AA3")),
        #NET "SPI_Flash_MISO"     LOC = "T14"    | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
        #NET "SPI_Flash_MOSI"     LOC = "AB20"   | IOSTANDARD = "LVCMOS33";                                                     # Bank = 2
        #Subsignal("dq", Pins("AB20", "AA20", "R13", "T14")),
        IOStandard("LVCMOS33"), Misc("SLEW=FAST")
    ),

    ## onBoard Leds
    # NET "Led<0>" LOC = "U18"; # Bank = 1, Pin name = IO_L52N_M1DQ15,       Sch name = LD0
    #("user_led", 0, Pins("U18")),

    # frontend switches / leds
    ("hdled", 0, Pins("J7"), IOStandard("LVCMOS15")),
    ("pwled", 0, Pins("H8"), IOStandard("LVCMOS15")), #pwled+ connected to 3.3V
    ("pwrsw", 0, Pins("F5"), IOStandard("LVCMOS15")),

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

    ## Opsis I2C Bus
    # Connected to both the EEPROM and the FX2.
    #
    ## 24AA02E48 - component U23
    # 2 Kbit Electrically Erasable PROM
    # Pre-programmed Globally Unique, 48-bit Node Address
    # The device is organized as two blocks of 128 x 8-bit memory with a 2-wire serial interface.
    ## \/ Strongly pulled (2k) to VCC3V3 via R34
    #NET "eeprom_scl"           LOC =     "G6"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SCL)
    #NET "eeprom_sda"           LOC =     "C1"       |IOSTANDARD =             I2C;     #                      (/Ethernet/MAC_SDA)
    ("opsis_i2c", 0,
        Subsignal("scl", Pins("G6"), IOStandard("I2C")),
        Subsignal("sda", Pins("C1"), IOStandard("I2C")),
    ),

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

    ## onboard HDMI IN2
    ## HDMI - connector J4 - Direction RX
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

    # Debug header?
    #("debug", 0, Pins("AA2"), IOStandard("LVCMOS15")), # (/FPGA_Bank_0_3/DEBUG_IO0)

    ## onboard HDMI OUT1
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
        Subsignal("scl", Pins("Y7"), IOStandard("I2C")),
        Subsignal("sda", Pins("Y10"), IOStandard("I2C")),
        Subsignal("hpd_notif", Pins("AB7"), IOStandard("LVCMOS33"))
    ),

    ## onboard HDMI OUT2
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
        Subsignal("scl", Pins("Y17"), IOStandard("I2C")),
        Subsignal("sda", Pins("AB17"), IOStandard("I2C")),
        Subsignal("hpd_notif", Pins("AB18"), IOStandard("LVCMOS33"))
    ),

    # FX2 USB Interface
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
    ("fx2_reset", 0, Pins("G22"), IOStandard("LVCMOS33"), Misc("PULLUP"), Misc("DRIVE=24"), Misc("SLEW=SLOW")),

    # To Cypress FX2 UART0
    # WARNING: This was labelled incorrectly - https://github.com/timvideos/HDMI2USB-numato-opsis-hardware/issues/13
    # Can be accessed via `opsis-mode-switch --mode=serial`
    # FIXME: Will be supported by `opsis-mode-switch --mode=jtag` longer term.
    ("fx2_serial", 0,
        # CY_RXD1 - P18 - Cypress RXD0
        Subsignal("tx", Pins("P18"), IOStandard("LVCMOS33")),
        # CY_TXD1 - T17 - Cypress TXD0
        Subsignal("rx", Pins("T17"), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ),
    # To Cypress FX2 UART1
    #("serial", 1,
    #    Subsignal("rx", Pins("A16"), IOStandard("LVCMOS33")),
    #    Subsignal("tx", Pins("B16"), IOStandard("LVCMOS33")),
    #),
    #

    # FIXME: This assumes a TOFE LowSpeedIO board is currently connected.
    # -----------------------------------
    ("tofe", 0,
        Subsignal("rst", Pins(tofe_pin("pcie_reset")), IOStandard("I2C"), Misc("PULLUP")),
        Subsignal("scl", Pins(tofe_pin("smclk")), IOStandard("I2C")),
        Subsignal("sda", Pins(tofe_pin("smdat")), IOStandard("I2C")),
    ),

    ("tofe_io",
        Subsignal("a_io_p", Pins(" ".join(p for n, p in sorted(_tofe_io.items()) if n.endswith('p') and 'io_a' in n))),
        Subsignal("a_io_n", Pins(" ".join(p for n, p in sorted(_tofe_io.items()) if n.endswith('n') and 'io_a' in n))),
        Subsignal("b_io_p", Pins(" ".join(p for n, p in sorted(_tofe_io.items()) if n.endswith('p') and 'io_b' in n))),
        Subsignal("b_io_n", Pins(" ".join(p for n, p in sorted(_tofe_io.items()) if n.endswith('n') and 'io_b' in n))),
    ),

    # serial
    ("tofe_lsio_serial", 0,
        Subsignal("tx", Pins(tofe_pin(tofe_low_speed_io("rx")))),
        Subsignal("rx", Pins(tofe_pin(tofe_low_speed_io("tx"))), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),

    # user leds
    ("tofe_lsio_user_led", 0, Pins(tofe_pin(tofe_low_speed_io("led1"))), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
    ("tofe_lsio_user_led", 1, Pins(tofe_pin(tofe_low_speed_io("led2"))), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
    ("tofe_lsio_user_led", 2, Pins(tofe_pin(tofe_low_speed_io("led3"))), IOStandard("LVCMOS33"), Misc("DRIVE=12")),
    ("tofe_lsio_user_led", 3, Pins(tofe_pin(tofe_low_speed_io("led4"))), IOStandard("LVCMOS33"), Misc("DRIVE=12")),

    # push buttons
    ("tofe_lsio_user_sw", 0, Pins(tofe_pin(tofe_low_speed_io("sw1"))), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("tofe_lsio_user_sw", 1, Pins(tofe_pin(tofe_low_speed_io("sw2"))), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("tofe_lsio_user_sw", 2, Pins(tofe_pin(tofe_low_speed_io("sw3"))), IOStandard("LVCMOS33"), Misc("PULLUP")),
    ("tofe_lsio_user_sw", 3, Pins(tofe_pin(tofe_low_speed_io("sw4"))), IOStandard("LVCMOS33"), Misc("PULLUP")),

    # PmodUSBUART or similar device connected to the "p3" Pmod connector.
    ("tofe_lsio_pmod_serial", 0,
        # PmodUSBUART - Pmod Type4 - UART
        # Pin 1 - CTS - In  - Peripheral can transmit
        # Pin 2 - TXD - Out - Data - Host to peripheral
        # Pin 3 - RXD - In  - Data - Peripheral to host
        # Pin 4 - RTS - Out - Peripheral ready for data
        # Pin 5 - GND
        # Pin 6 - VCC
        Subsignal("tx", Pins(tofe_pin(tofe_low_speed_pmod_io('p3', 2)))),
        Subsignal("rx", Pins(tofe_pin(tofe_low_speed_pmod_io('p3', 3))), Misc("PULLUP")),
        IOStandard("LVCMOS33")
    ),
]

pt = None
tofe_signals = [[], []]
for n, v in _tofe_io.items():
    if not n.startswith("diff"):
        continue

    _, t, p = n.split('_')

    if t != pt:
        assert len(tofe_signals[-1]) == len(tofe_signals[-2])

        tofe_signals.append(["{}_{}_{}".format(t, p[0], 'n')])
        tofe_signals.append(["{}_{}_{}".format(t, p[0], 'p')])
        pt = t

    if p.endswith('n'):
        tofe_signals[-2].append(n)
    elif p.endswith('p'):
        tofe_signals[-1].append(n)


## import pprint
## pprint.pprint(tofe_signals)
##
## pprint.pprint(list(
##    (i[0], (" ".join(_tofe_io[p] for p in i[1:])), IOStandard("LVCMOS33")) for i in tofe_signals[2:]))

_io.append(["tofe", 0]+[
    Subsignal(i[0], Pins(" ".join(_tofe_io[p] for p in i[1:])), IOStandard("LVCMOS33")) for i in tofe_signals[2:]
    ]
)


_connectors = [
]

_hdmi_infos = {
    "HDMI_OUT0_MNEMONIC": "TX1",
    "HDMI_OUT0_DESCRIPTION" : (
      "  The *first* HDMI port from the left.\\r\\n"
      "  Labeled J3 and HDMI Out 1.\\r\\n"
    ),

    "HDMI_OUT1_MNEMONIC": "TX2",
    "HDMI_OUT1_DESCRIPTION" : (
      "  The *second* HDMI port from the left.\\r\\n"
      "  Labeled J2 and HDMI Out 2.\\r\\n"
    ),

    "HDMI_IN0_MNEMONIC": "RX1",
    "HDMI_IN0_DESCRIPTION" : (
      "  The *third* HDMI port from the left.\\r\\n"
      "  Labeled J5 and HDMI In 1.\\r\\n"
    ),

    "HDMI_IN1_MNEMONIC": "RX2",
    "HDMI_IN1_DESCRIPTION" : (
      "  The *fourth* HDMI port from the left. (Closest to the USB.)\\r\\n"
      "  Labeled J4 and HDMI In 2.\\r\\n"
    ),
}


class Platform(XilinxPlatform):
    name = "opsis"
    default_clk_name = "clk100"
    default_clk_period = 10.0
    hdmi_infos = _hdmi_infos

    # W25Q128FVEIG - component U3
    # 128M (16M x 8) - 104MHz
    # Pretends to be a Micron N25Q128 (ID 0x0018ba20)
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_model = "n25q128"
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((128/8)*1024*1024) # 128Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000

    # The Opsis has a XC6SLX45 which bitstream takes up ~12Mbit (1484472 bytes)
    # 0x200000 offset (16Mbit) gives plenty of space
    gateware_size = 0x200000

    def __init__(self, programmer="openocd"):
        # XC6SLX45T-3FGG484C
        XilinxPlatform.__init__(self,  "xc6slx45t-fgg484-3", _io, _connectors)
        self.programmer = programmer

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

        # FPGA AUX is connected to the 3.3V supply
        self.add_platform_command("""CONFIG VCCAUX="3.3";""")

    def create_programmer(self):
	# Preferred programmer - Needs ixo-usb-jtag and latest openocd.
        proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
        if self.programmer == "openocd":
            return OpenOCD(config="board/numato_opsis.cfg", flash_proxy_basename=proxy)
	# Alternative programmers - not regularly tested.
        elif self.programmer == "urjtag":
            return UrJTAG(cable="USBBlaster")
        elif self.programmer == "impact":
            return iMPACT()
        else:
            raise ValueError("{} programmer is not supported".format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)

        # The oscillator clock sources.
        try:
            self.add_period_constraint(self.lookup_request("clk100"), 10.0)
        except ConstraintError:
            pass

        try:
            self.add_period_constraint(self.lookup_request("clk27"), 37.0)
        except ConstraintError:
            pass

        # HDMI input clock pins.
        for i in range(2):
            try:
                self.add_period_constraint(self.lookup_request("hdmi_in", i).clk_p, 12)
            except ConstraintError:
                pass

        # Ethernet input clock pins.
        try:
            self.add_period_constraint(self.lookup_request("eth_clocks").rx, 8.0)
        except ConstraintError:
            pass

        # USB input clock pins.
        try:
            self.add_period_constraint(self.lookup_request("fx2").ifclk, 10)
        except ConstraintError:
            pass
