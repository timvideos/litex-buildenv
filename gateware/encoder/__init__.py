import os

from migen.fhdl.std import *
from migen.bus import wishbone
from migen.genlib.record import *
from migen.bank.description import *
from migen.flow.actor import *
from migen.actorlib.fifo import SyncFIFO
from migen.actorlib import structuring, spi
from migen.bank.eventmanager import *

from misoclib.mem.sdram.frontend import dma_lasmi

from gateware.csc.ycbcr422to444 import YCbCr422to444


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
        chroma_upsampler = RenameClockDomains(YCbCr422to444(), "encoder")
        self.submodules += chroma_upsampler
        self.comb += [
            Record.connect(self.sink, chroma_upsampler.sink, leave_out=["data"]),
            chroma_upsampler.sink.y.eq(self.sink.data[:8]),
            chroma_upsampler.sink.cb_cr.eq(self.sink.data[8:])
        ]

        # output fifo
        output_fifo_almost_full = Signal()
        output_fifo = RenameClockDomains(SyncFIFO([("data", 8)], 1024), "encoder")
        self.submodules += output_fifo
        self.comb += [
            output_fifo_almost_full.eq(output_fifo.fifo.level > 1024-128),
            Record.connect(output_fifo.source, self.source)
        ]

        # Wishbone cross domain crossing
        jpeg_bus = wishbone.Interface()
        self.specials += Instance("wb_async_reg",
                            i_wbm_clk=ClockSignal(),
                            i_wbm_rst=ResetSignal(),
                            i_wbm_adr_i=self.bus.adr,
                            i_wbm_dat_i=self.bus.dat_w,
                            o_wbm_dat_o=self.bus.dat_r,
                            i_wbm_we_i=self.bus.we,
                            i_wbm_sel_i=self.bus.sel,
                            i_wbm_stb_i=self.bus.stb,
                            o_wbm_ack_o=self.bus.ack,
                            o_wbm_err_o=self.bus.err,
                            #o_wbm_rty_o=,
                            i_wbm_cyc_i=self.bus.cyc,

                            i_wbs_clk=ClockSignal("encoder"),
                            i_wbs_rst=ResetSignal("encoder"),
                            o_wbs_adr_o=jpeg_bus.adr,
                            i_wbs_dat_i=jpeg_bus.dat_r,
                            o_wbs_dat_o=jpeg_bus.dat_w,
                            o_wbs_we_o=jpeg_bus.we,
                            o_wbs_sel_o=jpeg_bus.sel,
                            o_wbs_stb_o=jpeg_bus.stb,
                            i_wbs_ack_i=jpeg_bus.ack,
                            i_wbs_err_i=jpeg_bus.err,
                            i_wbs_rty_i=0,
                            o_wbs_cyc_o=jpeg_bus.cyc)


        # encoder
        self.specials += Instance("JpegEnc",
                            i_CLK=ClockSignal("encoder"),
                            i_RST=ResetSignal("encoder"),

                            i_OPB_ABus=Cat(Signal(2), jpeg_bus.adr) & 0x3ff,
                            i_OPB_BE=jpeg_bus.sel,
                            i_OPB_DBus_in=jpeg_bus.dat_w,
                            i_OPB_RNW=~jpeg_bus.we,
                            i_OPB_select=jpeg_bus.stb & jpeg_bus.cyc,
                            o_OPB_DBus_out=jpeg_bus.dat_r,
                            o_OPB_XferAck=jpeg_bus.ack,
                            #o_OPB_retry=,
                            #o_OPB_toutSup=,
                            o_OPB_errAck=jpeg_bus.err,

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

        # add verilog sources
        platform.add_source(os.path.join(platform.soc_ext_path, "gateware", "encoder", "verilog", "wb_async_reg.v"))

        # bandwidth
        self.submodules.bandwidth = EncoderBandwidth() # XXX add CDC
        self.comb += self.bandwidth.nbytes_inc.eq(self.source.stb & self.source.ack)
