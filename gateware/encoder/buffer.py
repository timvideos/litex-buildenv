from migen.fhdl.std import *
from migen.genlib.record import *
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import chooser
from migen.flow.actor import *

class EncoderBuffer(Module):
    def __init__(self):
        self.sink = sink = Sink(EndpointDescription([("data", 128)], packetized=True))
        self.source = source = Source(EndpointDescription([("data", 16)], packetized=True))

        # # #

        # mem
        mem = Memory(128, 16)
        write_port = mem.get_port(write_capable=True)
        read_port = mem.get_port(async_read=True)
        self.specials += mem, write_port, read_port

        write_sel = Signal()
        write_swap = Signal()
        read_sel = Signal(reset=1)
        read_swap = Signal()
        self.sync += [
            If(write_swap,
                write_sel.eq(~write_sel)
            ),
            If(read_swap,
                read_sel.eq(~read_sel)
            )
        ]


        # write path
        v_write_clr = Signal()
        v_write_inc = Signal()
        v_write = Signal(3)
        self.sync += \
            If(v_write_clr,
                v_write.eq(0)
            ).Elif(v_write_inc,
                v_write.eq(v_write + 1)
            )

        self.comb += [
            write_port.adr.eq(v_write),
            write_port.adr[-1].eq(write_sel),
            write_port.dat_w.eq(sink.data),
            write_port.we.eq(sink.stb & sink.ack)
        ]

        self.submodules.write_fsm = write_fsm = FSM(reset_state="IDLE")
        write_fsm.act("IDLE",
            v_write_clr.eq(1),
            If(write_sel != read_sel,
                NextState("WRITE")
            )
        )
        write_fsm.act("WRITE",
            sink.ack.eq(1),
            If(sink.stb,
                If(v_write == 7,
                    write_swap.eq(1),
                    NextState("IDLE")
                ).Else(
                    v_write_inc.eq(1)
                )
            )
        )

        # read path
        h_read_clr = Signal()
        h_read_inc = Signal()
        h_read = Signal(3)
        self.sync += \
            If(h_read_clr,
                h_read.eq(0)
            ).Elif(h_read_inc,
                h_read.eq(h_read + 1)
            )

        v_read_clr = Signal()
        v_read_inc = Signal()
        v_read = Signal(3)
        self.sync += \
            If(v_read_clr,
                v_read.eq(0)
            ).Elif(v_read_inc,
                v_read.eq(v_read + 1)
            )

        self.comb += [
            read_port.adr.eq(v_read),
            read_port.adr[-1].eq(read_sel),
            chooser(read_port.dat_r, h_read, source.data, reverse=True)
        ]

        self.submodules.read_fsm = read_fsm = FSM(reset_state="IDLE")
        read_fsm.act("IDLE",
            h_read_clr.eq(1),
            v_read_clr.eq(1),
            If(read_sel == write_sel,
                read_swap.eq(1),
                NextState("READ")
            )
        )
        read_fsm.act("READ",
            source.stb.eq(1),
            source.sop.eq((h_read == 0) & (v_read == 0)),
            source.eop.eq((h_read == 7) & (v_read == 7)),
            If(source.ack,
                If(h_read == 7,
                    h_read_clr.eq(1),
                    If(v_read == 7,
                        NextState("IDLE")
                    ).Else(
                        v_read_inc.eq(1)
                    )
                ).Else(
                    h_read_inc.eq(1)
                )
            )
        )
