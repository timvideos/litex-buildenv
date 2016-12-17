import os

from litex.gen import *
from litex.gen.genlib.cdc import MultiReg
from litex.gen.genlib.misc import chooser

from litex.soc.interconnect import wishbone
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from litedram.frontend.dma import LiteDRAMDMAReader
from litevideo.csc.ycbcr422to444 import YCbCr422to444


class EncoderDMAReader(Module, AutoCSR):
    def __init__(self, dram_port):
        self.source = source = stream.Endpoint([("data", 128)])
        self.base = CSRStorage(32)
        self.h_width = CSRStorage(16)
        self.v_width = CSRStorage(16)
        self.start = CSR()
        self.done = CSRStatus()

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        pixel_bits = 16 # ycbcr 4:2:2
        burst_pixels = dram_port.dw//pixel_bits
        alignment_bits = bits_for(dram_port.dw//8) - 1

        self.comb += dma.source.connect(source) # XXX add Converter

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
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
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

        read_address = Signal(dram_port.aw + alignment_bits)
        self.comb += [
            read_address.eq(v * h_width + h),
            dma.sink.address.eq(base[alignment_bits:] +
                                read_address[alignment_bits - log2_int(pixel_bits//8):])
        ]


class EncoderBuffer(Module):
    def __init__(self):
        self.sink = sink = stream.Endpoint([("data", 128)])
        self.source = source = stream.Endpoint([("data", 16)])

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
            write_port.we.eq(sink.valid & sink.ready)
        ]

        self.submodules.write_fsm = write_fsm = FSM(reset_state="IDLE")
        write_fsm.act("IDLE",
            v_write_clr.eq(1),
            If(write_sel != read_sel,
                NextState("WRITE")
            )
        )
        write_fsm.act("WRITE",
            sink.ready.eq(1),
            If(sink.valid,
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
            source.valid.eq(1),
            source.last.eq((h_read == 7) & (v_read == 7)),
            If(source.ready,
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


class Encoder(Module, AutoCSR):
    def __init__(self, platform):
        self.sink = stream.Endpoint([("data", 16)])
        self.source = stream.Endpoint([("data", 8)])
        self.bus = wishbone.Interface()

        # # #

        # chroma upsampler
        self.submodules.chroma_upsampler = chroma_upsampler = YCbCr422to444()
        self.comb += [
            Record.connect(self.sink, chroma_upsampler.sink, omit=["data"]),
            chroma_upsampler.sink.y.eq(self.sink.data[:8]),
            chroma_upsampler.sink.cb_cr.eq(self.sink.data[8:])
        ]

        input_fifo = stream.SyncFIFO([("data", 24)], 128)
        self.submodules += input_fifo

        self.comb += [
            input_fifo.sink.valid.eq(chroma_upsampler.source.valid),
            input_fifo.sink.data.eq(Cat(chroma_upsampler.source.y,
                                        chroma_upsampler.source.cb,
                                        chroma_upsampler.source.cr)),
            chroma_upsampler.source.ready.eq(input_fifo.sink.ready)
        ]

        fdct_fifo_rd = Signal()
        fdct_fifo_q = Signal(24)
        fdct_fifo_hf_full = Signal()

        fdct_data_d1 = Signal(24)
        fdct_data_d2 = Signal(24)
        fdct_data_d3 = Signal(24)
        fdct_data_d4 = Signal(24)
        fdct_data_d5 = Signal(24)

        self.sync += [
            If(fdct_fifo_rd,
                fdct_data_d1.eq(input_fifo.source.data),
            ),
            fdct_data_d2.eq(fdct_data_d1),
            fdct_data_d3.eq(fdct_data_d2),
            fdct_data_d4.eq(fdct_data_d3),
            fdct_data_d5.eq(fdct_data_d4)
        ]
        self.comb += [
            fdct_fifo_q.eq(fdct_data_d4),
            fdct_fifo_hf_full.eq((input_fifo.level >= 64)),
            input_fifo.source.ready.eq(fdct_fifo_rd)
        ]

        # output fifo
        output_fifo_almost_full = Signal()
        self.submodules.output_fifo = output_fifo = stream.SyncFIFO([("data", 8)], 1024)
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

            o_fdct_fifo_rd=fdct_fifo_rd,
            i_fdct_fifo_q=fdct_fifo_q,
            i_fdct_fifo_hf_full=fdct_fifo_hf_full,
            #o_fdct_fifo_dval_o=,

            o_ram_byte=output_fifo.sink.data,
            o_ram_wren=output_fifo.sink.valid,
            #o_ram_wraddr=,
            #o_frame_size=,
            i_outif_almost_full=output_fifo_almost_full)

        # add vhdl sources
        platform.add_source_dir(os.path.join("gateware", "encoder", "vhdl"))
