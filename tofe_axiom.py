
_tofe_axiom = {
    # North Connector
    "north": {
        # I2C Eeprom
        "sda": "diff_clk_b1p",
        "scl": "diff_clk_b1n",

        # IO pins
        "io0": "diff_clk_xp",
        "io1": "diff_io_b6n",
        "io2": "diff_io_b6p",
        "io3": "diff_io_zn",
        "io4": "diff_io_yn",
        "io5": "diff_io_xn",
        "io6": "diff_io_b0n",
        "io7": "diff_io_b0p",

        # LVDS Pairs
        "lvds_0p": "diff_io_b1p",
        "lvds_0n": "diff_io_b1n",

        "lvds_1p": "diff_io_b2p",
        "lvds_1n": "diff_io_b2n",

        "lvds_2p": "diff_io_b3p",
        "lvds_2n": "diff_io_b3n",

        "lvds_3p": "diff_clk_b0p",
        "lvds_3n": "diff_clk_b0n",

        "lvds_4p": "diff_io_b4p",
        "lvds_4n": "diff_io_b4n",

        "lvds_5p": "diff_io_b5p",
        "lvds_5n": "diff_io_b5n",
    }

    # South Connector
    "south": {
        # I2C Eeprom
        "sda": "diff_clk_a1p",
        "scl": "diff_clk_a1n",

        # IO pins
        "io0": "diff_clk_xn",
        "io1": "diff_io_a6n",
        "io2": "diff_io_a6p",
        "io3": "diff_io_zp",
        "io4": "diff_io_yp",
        "io5": "diff_io_xp",
        "io6": "diff_io_a0n",
        "io7": "diff_io_a0p",

        # LVDS Pairs
        "lvds_0p": "diff_io_a1p",
        "lvds_0n": "diff_io_a1n",

        "lvds_1p": "diff_io_a2p",
        "lvds_1n": "diff_io_a2n",

        "lvds_2p": "diff_io_a3p",
        "lvds_2n": "diff_io_a3n",

        "lvds_3p": "diff_clk_a0p",
        "lvds_3n": "diff_clk_a0n",

        "lvds_4p": "diff_io_a4p",
        "lvds_4n": "diff_io_a4n",

        "lvds_5p": "diff_io_a5p",
        "lvds_5n": "diff_io_a5n",
    }
}

_axiom_hdmi = {
    # Control Signals
    #"io0": None,
    "io1": "eq0",
    "io2": "ihp",
    "io3": "ddet",
    "io4": "eq1",
    "io5": "ddc_en",
    "io6": "oe",
    "io7": "en",

    # LVDS Pairs
    "lvds_0p": "data2_p",
    "lvds_0n": "data2_n",

    "lvds_1p": "data1_p",
    "lvds_1n": "data1_n",

    "lvds_2p": "data0_p",
    "lvds_2n": "data0_n",

    "lvds_3p": "clk_p",
    "lvds_3n": "clk_n",

    #"lvds_4p": None,
    #"lvds_4n": None,

    "lvds_5p": "scl",
    "lvds_5n": "sda",
}
