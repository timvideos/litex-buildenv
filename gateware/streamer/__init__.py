import os

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *
from migen.actorlib.fifo import SyncFIFO, AsyncFIFO
from migen.genlib.misc import WaitTimer

class USBStreamer(Module):
    def __init__(self, platform, pads):
        self.sink = sink = Sink([("data", 8)])

        # # #

        self.clock_domains.cd_usb = ClockDomain()
        self.comb += [
          self.cd_usb.clk.eq(pads.ifclk),
          self.cd_usb.rst.eq(ResetSignal()) # XXX FIXME
        ]

        self.submodules.fifo = fifo = RenameClockDomains(AsyncFIFO([("data", 8)], 4),
                                          {"write": "sys", "read": "usb"})
        self.comb += Record.connect(sink, fifo.sink)


        self.specials += Instance("fx2_jpeg_streamer",
                                  # clk, rst
                                  i_rst=ResetSignal("usb"),
                                  i_clk=ClockSignal("usb"),

                                  # jpeg encoder interface
                                  i_sink_stb=fifo.source.stb,
                                  i_sink_data=fifo.source.data,
                                  o_sink_ack=fifo.source.ack,

                                  # cypress fx2 slave fifo interface
                                  io_fx2_data=pads.data,
                                  i_fx2_full_n=pads.flagb,
                                  i_fx2_empty_n=pads.flagc,
                                  o_fx2_addr=pads.addr,
                                  o_fx2_cs_n=pads.cs_n,
                                  o_fx2_wr_n=pads.wr_n,
                                  o_fx2_rd_n=pads.rd_n,
                                  o_fx2_oe_n=pads.oe_n,
                                  o_fx2_pktend_n=pads.pktend_n
        )

        # add VHDL sources
        platform.add_source_dir(os.path.join(platform.soc_ext_path, "gateware", "streamer", "vhdl"))
