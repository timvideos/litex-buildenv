import os

from litex.gen import *
from litex.gen.genlib.cdc import MultiReg

from litex.soc.interconnect import wishbone
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *
from litex.soc.interconnect.csr_eventmanager import *

from litedram.frontend.dma import LiteDRAMDMAReader
from litevideo.csc.ycbcr422to444 import YCbCr422to444


# XXX needs cleanup
class EncoderDMAReader(Module, AutoCSR):
    def __init__(self, dram_port):
        self.shoot = CSR()
        self.done = CSRStatus()
        self.base = CSRStorage(dram_port.aw)
        self.length = CSRStorage(dram_port.aw)

        self.source = source = stream.Endpoint([("data", 16)])

        # # #

        self.submodules.dma = dma = LiteDRAMDMAReader(dram_port)

        shoot = Signal()
        self.comb += shoot.eq(self.shoot.re & self.shoot.r)

        shooted = Signal()
        address_counter = Signal(dram_port.aw)
        address_counter_ce = Signal()
        data_counter = Signal(dram_port.aw)
        data_counter_ce = Signal()
        self.sync += [
            If(shoot,
                shooted.eq(1)
            ),
            If(shoot,
                address_counter.eq(0)
            ).Elif(address_counter_ce,
                address_counter.eq(address_counter + 1)
            ),
            If(shoot,
                data_counter.eq(0),
            ).Elif(data_counter_ce,
                data_counter.eq(data_counter + 1)
            )
        ]

        address_enable = Signal()
        self.comb += address_enable.eq(shooted & (address_counter != (self.length.storage - 1)))

        self.comb += [
            dma.sink.valid.eq(address_enable),
            dma.sink.address.eq(self.base.storage + address_counter),
            address_counter_ce.eq(address_enable & dma.sink.ready)
        ]

        data_enable = Signal()
        self.comb += data_enable.eq(shooted & (data_counter != (self.length.storage - 1)))
        self.comb += data_counter_ce.eq(dma.source.valid & dma.source.ready)

        self.comb += self.done.status.eq(~data_enable & ~address_enable)

        self.submodules.converter = stream.Converter(dram_port.dw, 16, reverse=True)
        self.comb += [
            self.dma.source.connect(self.converter.sink),
            self.converter.source.connect(self.source)
        ]


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
        self.reset = CSR()
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
                            i_RST=ResetSignal() | (self.reset.r & self.reset.re),

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

        # bandwidth
        self.submodules.bandwidth = EncoderBandwidth()
        self.comb += self.bandwidth.nbytes_inc.eq(self.source.valid & self.source.ready)
