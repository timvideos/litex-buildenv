from migen.fhdl.std import *
from migen.bank.description import *
from migen.genlib.fsm import FSM, NextState


class DNA(Module, AutoCSR):
    def __init__(self):
        self._id = CSRStatus(64)

        # # #

        read = Signal()
        shift = Signal()
        cnt = Signal(6)
        done = Signal()
        data = self._id.status
        dout = Signal()

        self.specials += Instance("DNA_PORT",
                i_CLK=ClockSignal("base50"),
                i_READ=read,
                i_SHIFT=shift,
                i_DIN=Signal(),
                o_DOUT=dout
        )

        self.sync.base50 += \
            If(shift,
             cnt.eq(cnt + 1),
             data.eq(Cat(data[1:], dout))
            )
        self.comb += done.eq(cnt == 63)

        fsm = RenameClockDomains(FSM(reset_state="IDLE"), "base50")
        self.submodules += fsm

        fsm.act("IDLE",
            read.eq(1),
            NextState("READ")
        )
        fsm.act("READ",
            shift.eq(1),
            If(done, NextState("END"))
        )
        fsm.act("END",
            NextState("END")
        )
