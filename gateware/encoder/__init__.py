import os

from migen.fhdl.std import *
from migen.bus import wishbone
from migen.genlib.record import *
from migen.genlib.cdc import MultiReg
from migen.bank.description import *
from migen.flow.actor import *
from migen.flow.network import *
from migen.actorlib.fifo import SyncFIFO
from migen.actorlib import structuring, spi
from migen.bank.eventmanager import *

from misoclib.mem.sdram.frontend import dma_lasmi

from gateware.csc.ycbcr422to444 import YCbCr422to444
from gateware.csc.ymodulator import YModulator


class EncoderReader(Module, AutoCSR):
    def __init__(self, lasmim):
        self.source = source = Source(EndpointDescription([("data", 16)], packetized=True))

        reader = dma_lasmi.Reader(lasmim)
        self.dma = spi.DMAReadController(reader, mode=spi.MODE_SINGLE_SHOT)

        pack_factor = lasmim.dw//16
        packed_dat = structuring.pack_layout(16, pack_factor)
        cast = structuring.Cast(lasmim.dw, packed_dat)
        unpack = structuring.Unpack(pack_factor, [("data", 16)], reverse=True)


        # graph
        g = DataFlowGraph()
        g.add_pipeline(self.dma, cast, unpack)
        self.submodules += CompositeActor(g)
        self.comb += Record.connect(unpack.source, source)

        self.sync += \
            If(self.dma._busy.status == 0,
                source.sop.eq(1),
            ).Elif(source.stb & source.ack,
                source.sop.eq(0)
            )

        # irq
        self.submodules.ev = EventManager()
        self.ev.done = EventSourceProcess()
        self.ev.finalize()
        self.comb += self.ev.done.trigger.eq(self.dma._busy.status)


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
        self.sink = Sink(EndpointDescription([("data", 16)], packetized=True))
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

        # encoder fifo 
        encoder_fifo_full = Signal()
        self.comb += chroma_upsampler.source.ack.eq(~encoder_fifo_full)

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

                            i_iram_wdata=Cat(chroma_upsampler.source.y,
                                             chroma_upsampler.source.cb,
                                             chroma_upsampler.source.cr),
                            i_iram_wren=chroma_upsampler.source.stb & ~encoder_fifo_full,
                            o_iram_fifo_afull=encoder_fifo_full,

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
