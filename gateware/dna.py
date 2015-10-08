from migen.fhdl.std import *
from migen.bank.description import *
from migen.genlib.fsm import FSM, NextState


class DNA(Module, AutoCSR):
    def __init__(self):
        self._id = CSRStatus(64)

        # # #

        self.clock_domains.cd_dna = ClockDomain("dna")
        read = Signal()
        shift = Signal()
        cnt = Signal(6)
        done = Signal()
        data = self._id.status
        dout = Signal()


        # use BUFR to divide clock (Switching limit on DNA)
        dna_clk = Signal()
        self.specials += Instance("BUFR",
                p_BUFR_DIVIDE="8",
                i_CE=1,
                i_CLR=0,
                i_I=ClockSignal(),
                o_O=dna_clk,
        )
        self.specials += Instance("BUFG",
                i_I=dna_clk,
                o_O=ClockSignal("dna"),
        )
        self.comb += self.cd_dna.rst.eq(ResetSignal())

        self.specials += Instance("DNA_PORT",
                i_CLK=ClockSignal("dna"),
                i_READ=read,
                i_SHIFT=shift,
                i_DIN=Signal(),
                o_DOUT=dout
        )

        self.sync.dna += \
            If(shift,
             cnt.eq(cnt + 1),
             data.eq(Cat(data[1:], dout))
            )
        self.comb += done.eq(cnt == 63)

        fsm = RenameClockDomains(FSM(reset_state="IDLE"), "dna")
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
