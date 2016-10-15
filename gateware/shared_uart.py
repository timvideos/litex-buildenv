
"""
UART which is connected to multiple sets of pins.
"""

import operator

from litex.gen import *

from litex.soc.cores import uart


class SharedUART(Module):

    def __init__(self, clk_freq, baud_rate):
        self.tx = Signal()
        self.rx = Signal()
        self.tx_signals = []
        self.rx_signals = []

        self.submodules.phy = uart.RS232PHY(self, clk_freq, baud_rate)
        self.submodules.uart = uart.UART(self.phy)

    def add_uart_pads(self, new_pads):
        self.tx_signals.append(new_pads.tx)
        self.rx_signals.append(new_pads.rx)

    def do_finalize(self):
        for tx_sig in self.tx_signals:
            self.comb += [
                # TX
                tx_sig.eq(self.tx),
            ]

        self.comb += [
            # RX
            self.rx.eq(reduce(operator.__and__, self.rx_signals))
        ]


# FIXME: Add a test for the shared UART
