"""Module for talking to TOFE boards."""

from migen.fhdl import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.interconnect.csr import *

from gateware import i2c


class TOFE(Module, AutoCSR):
    """Common TOFE parts."""

    def __init__(self, platform):
        # TOFE board
        tofe_pads = platform.request('tofe')
        self.submodules.i2c = i2c.I2C(tofe_pads)

        # Use a proper Tristate for the reset signal so the "pull up" works.
        tofe_reset = TSTriple(1)
        self.comb += [
            tofe_reset.o.eq(0),
        ]
        self.specials += [
            tofe_reset.get_tristate(tofe_pads.rst),
        ]
        self.submodules.rst = GPIOOut(tofe_reset.oe)


class TOFELowSpeedIO(TOFE):
    """TOFE LowSpeedIO board."""

    def __init__(self, platform, shared_uart):
        TOFE.__init__(self, platform)

        # UARTs
        shared_uart.add_uart_pads(platform.request('tofe_lsio_serial'))
        shared_uart.add_uart_pads(platform.request('tofe_lsio_pmod_serial'))

        # LEDs
        lsio_leds = Signal(4)
        self.submodules.lsio_leds = GPIOOut(lsio_leds)
        self.comb += [
            platform.request('tofe_lsio_user_led', 0).eq(lsio_leds[0]),
            platform.request('tofe_lsio_user_led', 1).eq(lsio_leds[1]),
            platform.request('tofe_lsio_user_led', 2).eq(lsio_leds[2]),
            platform.request('tofe_lsio_user_led', 3).eq(lsio_leds[3]),
        ]
        # Switches
        lsio_sws = Signal(4)
        self.submodules.lsio_sws = GPIOIn(lsio_sws)
        self.comb += [
            lsio_sws[0].eq(~platform.request('tofe_lsio_user_sw', 0)),
            lsio_sws[1].eq(~platform.request('tofe_lsio_user_sw', 1)),
            lsio_sws[2].eq(~platform.request('tofe_lsio_user_sw', 2)),
            lsio_sws[3].eq(~platform.request('tofe_lsio_user_sw', 3)),
        ]


class TOFE2AXIOM(TOFE):
    """TOFE to AXIOM Adapter board."""
    pass


def TOFEBoard(name):
    if name.lower() == "lowspeedio":
        return TOFELowSpeedIO
    elif name.lower() == "axiom":
        return TOFELowSpeedIO
    else:
        return TOFE
