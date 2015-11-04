import os

from migen.fhdl.std import *
from migen.bus import wishbone
from migen.genlib.record import *
from migen.genlib.cdc import MultiReg
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import chooser
from migen.bank.description import *
from migen.flow.actor import *
from migen.flow.network import *
from migen.actorlib.fifo import SyncFIFO
from migen.actorlib import structuring, spi
from migen.bank.eventmanager import *

from misoclib.mem.sdram.frontend import dma_lasmi

from gateware.csc.ycbcr422to444 import YCbCr422to444


class EncoderReader(Module, AutoCSR):
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

        base = self.base.storage
        h_width = self.h_width.storage
        v_width = self.v_width.storage
        start = self.start.r & self.start.re
        done = self.done.status

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


class EncoderBuffer(Module):
    def __init__(self, dw):
        self.sink = sink = Sink(EndpointDescription([("data", 128)]))
        self.source = source = Source(EndpointDescription([("data", 16)]))

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


class EncoderBandwidth(Module, AutoCSR):
    def __init__(self):
        self.nbytes_inc = Signal()
        self.nbytes_clear = CSR()
        self.nbytes = CSRStatus(32)

        # # #

        nbytes_clear = self.nbytes_clear.re & self.nbytes_clear.r
        nbytes = self.nbytes.status

        self.sync += \
            If(nbytes_clear,
                nbytes.eq(0)
            ).Elif(self.nbytes_inc ,
                nbytes.eq(nbytes + 1)
            )


class Encoder(Module, AutoCSR):
    def __init__(self, platform):
        self.sink = Sink(EndpointDescription([("data", 16)]))
        self.source = Source([("data", 8)])
        self.bus = wishbone.Interface()

        # # #

        # chroma upsampler
        self.submodules.chroma_upsampler = chroma_upsampler = YCbCr422to444()
        self.comb += [
            Record.connect(self.sink, chroma_upsampler.sink, leave_out=["data"]),
            chroma_upsampler.sink.y.eq(self.sink.data[:8]),
            chroma_upsampler.sink.cb_cr.eq(self.sink.data[8:])
        ]

        # output fifo
        output_fifo_almost_full = Signal()
        self.submodules.output_fifo = output_fifo = SyncFIFO([("data", 8)], 1024)
        self.comb += [
            output_fifo_almost_full.eq(output_fifo.fifo.level > 1024-128),
            Record.connect(output_fifo.source, self.source)
        ]

        # encoder
        self.specials += Instance("JpegEnc",
                            i_CLK=ClockSignal(),
                            i_RST=ResetSignal(),

                            i_OPB_ABus=Cat(Signal(2), self.bus.adr) & 0x3ff,
                            i_OPB_BE=self.bus.sel,
                            i_OPB_DBus_in=self.bus.dat_w,
                            i_OPB_RNW=~self.bus.we,
                            i_OPB_select=self.bus.stb & self.bus.cyc,
                            o_OPB_DBus_out=self.bus.dat_r,
                            o_OPB_XferAck=self.bus.ack,
                            #o_OPB_retry=,
                            #o_OPB_toutSup=,
                            o_OPB_errAck=self.bus.err,

                            i_fdct_ack=chroma_upsampler.source.ack,
                            i_fdct_stb=chroma_upsampler.source.stb,
                            i_fdct_data=Cat(chroma_upsampler.source.y,
                                            chroma_upsampler.source.cb,
                                            chroma_upsampler.source.cr),

                            o_ram_byte=output_fifo.sink.data,
                            o_ram_wren=output_fifo.sink.stb,
                            #o_ram_wraddr=,
                            #o_frame_size=,
                            i_outif_almost_full=output_fifo_almost_full)
        # add vhdl sources
        platform.add_source_dir(os.path.join(platform.soc_ext_path, "gateware", "encoder", "vhdl"))

        # bandwidth
        self.submodules.bandwidth = EncoderBandwidth()
        self.comb += self.bandwidth.nbytes_inc.eq(self.source.stb & self.source.ack)
