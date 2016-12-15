import os

from litex.gen import *
from litex.gen.genlib.cdc import MultiReg

from litex.soc.interconnect import wishbone
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from litedram.frontend.dma import LiteDRAMDMAReader
from litevideo.csc.ycbcr422to444 import YCbCr422to444


class EncoderDMAReader(Module, AutoCSR):
    def __init__(self, dram_port):
        self.shoot = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(32)
        self.length = CSRStorage(32)

        self.source = source = stream.Endpoint([("data", 16)])

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        fsm = FSM(reset_state="IDLE")
        self.submodules += fsm

        shift = log2_int(dram_port.dw//8)
        base = Signal(dram_port.aw)
        length = Signal(dram_port.aw)
        offset = Signal(dram_port.aw)
        self.comb += [
            base.eq(self.base.storage[shift:]),
            length.eq(self.length.storage[shift:])
        ]

        fsm.act("IDLE",
            self.done.status.eq(1),
            If(self.shoot.re & self.shoot.r,
                NextValue(offset, 0),
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            dma.sink.valid.eq(1),
            If(dma.sink.ready,
                NextValue(offset, offset + 1),
                If(offset == (length-1),
                    NextState("IDLE")
                )
            )
        )
        self.comb += dma.sink.address.eq(base + offset)

        self.submodules.converter = stream.Converter(dram_port.dw, 16, reverse=True)
        self.comb += [
            self.dma.source.connect(self.converter.sink),
            self.converter.source.connect(self.source)
        ]


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

        # encoder fifo
        encoder_fifo_full = Signal()
        self.comb += chroma_upsampler.source.ready.eq(~encoder_fifo_full)

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

                            i_iram_wdata=Cat(chroma_upsampler.source.y,
                                             chroma_upsampler.source.cb,
                                             chroma_upsampler.source.cr),
                            i_iram_wren=chroma_upsampler.source.valid & ~encoder_fifo_full,
                            o_iram_fifo_afull=encoder_fifo_full,

                            o_ram_byte=output_fifo.sink.data,
                            o_ram_wren=output_fifo.sink.valid,
                            #o_ram_wraddr=,
                            #o_frame_size=,
                            i_outif_almost_full=output_fifo_almost_full)
        # add vhdl sources
        platform.add_source_dir(os.path.join("gateware", "encoder", "vhdl"))
