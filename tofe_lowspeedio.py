
_tofe_low_speed_io = {
    # UART interface
    "tx": "diff_io_xp", # UART->Host
    "rx": "diff_io_xn", # Host->UART

    # LEDs
    "led1": "diff_io_a5p",
    "led2": "diff_io_a5n",
    "led3": "diff_io_b6n",
    "led4": "diff_io_a6p",

    # Push buttons
    "sw1": "diff_clk_b0p",
    "sw2": "diff_clk_b1n",
    "sw3": "diff_clk_a1p",
    "sw4": "diff_clk_a1n",

    # PMOD - P1
    "gpio0_n": "diff_io_a0n",
    "gpio0_p": "diff_io_a0p",
    "gpio1_n": "diff_io_b0n",
    "gpio1_p": "diff_io_b0p",
    "gpio2_n": "diff_clk_xn",
    "gpio2_p": "diff_clk_xp",
    "gpio3_n": "diff_io_a1n",
    "gpio3_p": "diff_io_a1p",
    # PMOD - P2
    "gpio4_n": "diff_io_a2n",
    "gpio4_p": "diff_io_a2p",
    "gpio5_n": "diff_io_a3n",
    "gpio5_p": "diff_io_a3p",
    "gpio6_n": "diff_clk_a0n",
    "gpio6_p": "diff_clk_a0p",
    "gpio7_n": "diff_io_a4n",
    "gpio7_p": "diff_io_a4p",

    # Arduino Zero header (shared with PMOD - P3 & P4)
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
}

def tofe_low_speed_io(lowspeedio_netname):
    """Return the TOFE signal name associated with LowSpeedIO net name."""
    return _tofe_low_speed_io[lowspeedio_netname]

_tofe_low_speed_pmod_io = {
   # '<pmod name>': { <pin>: '<net name>', .... }
   # Pin  1, Pin  2, Pin  3, Pin  4, Pin  5 (GND), Pin  6 (VCC) - Outside Row / Top
   # Pin  7, Pin  8, Pin  9, Pin 10, Pin 11 (GND), Pin 12 (VCC) - Inside Row / Bottom

   # WARNING: On the older revisions of the board, the silk screen has labels
   # for Pin 2/11 on the Pmod connectors which are *wrong*.

   # Dedicated Pmod connectors
  'p1': {
      1: "gpio0_p", 2: "gpio1_p", 3: "gpio2_p", 4: "gpio3_n",
      7: "gpio0_n", 8: "gpio1_n", 9: "gpio2_n", 10: "gpio3_p",
  },
  'p2': {
      1: "gpio4_p", 2: "gpio4_n", 3: "gpio5_p", 4: "gpio5_n",
      7: "gpio6_p", 8: "gpio6_n", 9: "gpio7_p", 10: "gpio7_n",
  },
  # Pmods shared with the Arduino Zero header
  'p3': {
      1: "d9", 2: "d11", 3: "d13", 4: "d15",
      7: "d8", 8: "d10", 9: "d12", 10: "d14",
  },
  'p4': {
      1: "d1", 2: "d3", 3: "d5", 4: "d7",
      7: "d0", 8: "d2", 9: "d4", 10: "d6",
  },
}

def tofe_low_speed_pmod_io(pmod_name, pin):
    """Return the TOFE signal name associated with Pmod pin."""
    return tofe_low_speed_io(_tofe_low_speed_pmod_io[pmod_name][pin])
