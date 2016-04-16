import os

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.genlib.fsm import FSM, NextState
from migen.bank.description import *
from migen.flow.actor import *
from migen.actorlib.fifo import SyncFIFO
from migen.actorlib import structuring, spi

from misoclib.mem.sdram.frontend import dma_lasmi


class EncoderDMAReader(Module, AutoCSR):
    def __init__(self, lasmim):
        self.source = source = Source(EndpointDescription([("data", 128)]))
        self.base = CSRStorage(32)
        self.h_width = CSRStorage(16)
        self.v_width = CSRStorage(16)
        self.start = CSR()
        self.done = CSRStatus()

        # # #

        pixel_bits = 16 # ycbcr 4:2:2
        burst_pixels = lasmim.dw//pixel_bits
        alignment_bits = bits_for(lasmim.dw//8) - 1

        self.submodules.reader = reader = dma_lasmi.Reader(lasmim)
        self.submodules.converter = structuring.Converter(EndpointDescription([("data", lasmim.dw)]),
                                                          EndpointDescription([("data", 128)]),
                                                          reverse=True)
        self.comb += [
            Record.connect(reader.data, self.converter.sink, leave_out=set(["d"])),
            self.converter.sink.data.eq(reader.data.d),
            Record.connect(self.converter.source, source)
        ]

        base = Signal(32)
        h_width = self.h_width.storage
        v_width = self.v_width.storage
        start = self.start.r & self.start.re
        done = self.done.status
        self.sync += If(start, base.eq(self.base.storage))

        h_clr = Signal()
        h_clr_lsb = Signal()
        h_inc = Signal()
        h = Signal(16)
        h_next = Signal(16)
        self.comb += h_next.eq(h + burst_pixels)
        self.sync += \
            If(h_clr,
                h.eq(0)
            ).Elif(h_clr_lsb,
                h[:3].eq(0),
                h[3:].eq(h[3:])
            ).Elif(h_inc,
                h.eq(h_next)
            )

        v_clr = Signal()
        v_inc = Signal()
        v_dec7 = Signal()
        v = Signal(16)
        self.sync += \
            If(v_clr,
                v.eq(0)
            ).Elif(v_inc,
                v.eq(v + 1)
            ).Elif(v_dec7,
                v.eq(v - 7)
            )

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            h_clr.eq(1),
            v_clr.eq(1),
            If(start,
                NextState("READ")
            ).Else(
                done.eq(1)
            )
        )
        fsm.act("READ",
            reader.address.stb.eq(1),
            If(reader.address.ack,
                # last burst of 8 pixels
                If(h_next[:3] == 0,
                    # last line of a block of 8 pixels
                    If(v[:3] == 7,
                        # last block of a line
                        If(h >= h_width - burst_pixels,
                            h_clr.eq(1),
                            v_inc.eq(1),
                            # last line
                            If(v >= v_width - 1,
                                NextState("IDLE")
                            )
                        ).Else(
                            h_inc.eq(1),
                            v_dec7.eq(1)
                        )
                    ).Else(
                        h_clr_lsb.eq(1),
                        v_inc.eq(1)
                    )
                ).Else(
                    h_inc.eq(1)
                )
             )
        )

        read_address = Signal(lasmim.aw + alignment_bits)
        self.comb += [
            read_address.eq(v * h_width + h),
            reader.address.a.eq(base[alignment_bits:] +
            	                read_address[alignment_bits - log2_int(pixel_bits//8):])
        ]
