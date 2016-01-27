from migen.fhdl.std import *
from migen.bank.description import *
from migen.genlib.misc import optree
from migen.genlib.cdc import PulseSynchronizer

from gateware.hdmi_in.common import control_tokens


class WER(Module, AutoCSR):
    """Word Error Rate calculation module.

    https://en.wikipedia.org/wiki/Transition-minimized_differential_signaling

    """

    def __init__(self, period_bits=24):
        self.data = Signal(10)
        self._update = CSR()
        self._value = CSRStatus(period_bits)

        ###

        # pipeline stage 1
        # we ignore the 10th (inversion) bit, as it is independent of the transition minimization
        data_r = Signal(9)
        self.sync.pix += data_r.eq(self.data[:9])

        # pipeline stage 2
	# Count the number of transitions in the TMDS word.
        transitions = Signal(8)
        self.comb += [transitions[i].eq(data_r[i] ^ data_r[i+1]) for i in range(8)]
        transition_count = Signal(max=9)
        self.sync.pix += transition_count.eq(optree("+", [transitions[i] for i in range(8)]))

	# Control data characters are designed to have a large number (7) of
	# transitions to help the receiver synchronize its clock with the
	# transmitter clock.
        is_control = Signal()
        self.sync.pix += is_control.eq(optree("|", [data_r == ct for ct in control_tokens]))

        # pipeline stage 3
        is_error = Signal()
        self.sync.pix += is_error.eq((transition_count > 4) & ~is_control)

        # counter
        period_counter = Signal(period_bits)
        period_done = Signal()
        self.sync.pix += Cat(period_counter, period_done).eq(period_counter + 1)

        wer_counter = Signal(period_bits)
        wer_counter_r = Signal(period_bits)
        wer_counter_r_updated = Signal()
        self.sync.pix += [
            wer_counter_r_updated.eq(period_done),
            If(period_done,
                wer_counter_r.eq(wer_counter),
                wer_counter.eq(0)
            ).Elif(is_error,
                wer_counter.eq(wer_counter + 1)
            )
        ]

        # sync to system clock domain
        wer_counter_sys = Signal(period_bits)
        self.submodules.ps_counter = PulseSynchronizer("pix", "sys")
        self.comb += self.ps_counter.i.eq(wer_counter_r_updated)
        self.sync += If(self.ps_counter.o, wer_counter_sys.eq(wer_counter_r))

        # register interface
        self.sync += If(self._update.re, self._value.status.eq(wer_counter_sys))
