import os

from migen.fhdl.std import *
from migen.bus import wishbone
from migen.genlib.record import *
from migen.flow.actor import *
from migen.flow.network import *
from migen.actorlib.fifo import SyncFIFO
from migen.actorlib import structuring, spi
from migen.bank.eventmanager import *

from misoclib.mem.sdram.frontend import dma_lasmi


class JPEGEncoder(Module):
    def __init__(self, platform):
        self.sink = Sink([("data", 30)])
        self.source = Source([("data", 8)])
        self.bus = wishbone.Interface()

        # # #

        data = Signal(24)
        self.comb += [
          data[0:8].eq(self.sink.data[2:10]),
          data[8:16].eq(self.sink.data[12:20]),
          data[16:24].eq(self.sink.data[22:30])
        ]

        fifo = SyncFIFO([("data", 8)], 128)
        self.submodules += fifo

        self.specials += Instance("JpegEnc",
                                   #p_C_PIXEL_BITS=24,

                                   i_CLK=ClockSignal(),
                                   i_RST=ResetSignal(),

                                   i_OPB_ABus=Cat(Signal(2), self.bus.adr),
                                   i_OPB_BE=self.bus.sel,
                                   i_OPB_DBus_in=self.bus.dat_w,
                                   i_OPB_RNW=~self.bus.we,
                                   i_OPB_select=self.bus.stb & self.bus.cyc,
                                   o_OPB_DBus_out=self.bus.dat_r,
                                   o_OPB_XferAck=self.bus.ack,
                                   #o_OPB_retry=,
                                   #o_OPB_toutSup=,
                                   o_OPB_errAck=self.bus.err,

                                   i_iram_wdata=data,
                                   i_iram_wren=self.sink.stb & self.sink.ack,
                                   o_iram_fifo_afull=self.sink.ack,

                                   o_ram_byte=fifo.sink.data,
                                   o_ram_wren=fifo.sink.stb,
                                   #o_ram_wraddr=,
                                   i_outif_almost_full=(fifo.fifo.level < 64 + 16),

                                   #o_frame_size=
                                   )

        self.comb += Record.connect(fifo.source, self.source)

        # add Verilog sources
        #platform.add_source_dir(os.path.join(platform.soc_ext_path, "hdl", "jpeg_encoder", "verilog"))

        # add VHDL sources
        platform.add_source_dir(os.path.join(platform.soc_ext_path, "hdl", "jpeg_encoder", "vhd"))

class JPEGDMA(Module):
    def __init__(self, lasmim):
        self.source = Source([("data", 32)])

        reader = dma_lasmi.Reader(lasmim)
        self.dma = spi.DMAReadController(reader, spi.MODE_SINGLE_SHOT)

        pack_factor = lasmim.dw//32
        packed_dat = structuring.pack_layout(32, pack_factor)
        cast = structuring.Cast(lasmim.dw, packed_dat)
        unpack = structuring.Unpack(pack_factor, [("data", 32)])


        # Graph
        g = DataFlowGraph()
        g.add_pipeline(self.dma, cast, unpack)
        self.submodules += CompositeActor(g)
        self.comb += Record.connect(unpack.source, self.source)


        # Irq
        self.submodules.ev = EventManager()
        self.ev.done = EventSourceProcess()
        self.ev.finalize()
        self.comb += self.ev.done.trigger.eq(self.dma._busy.status)
