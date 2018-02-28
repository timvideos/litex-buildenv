import os

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect import stream

class USBStreamer(Module):
    def __init__(self, platform, pads):
        self.sink = sink = stream.Endpoint([("data", 8)])

        # # #

        self.clock_domains.cd_usb = ClockDomain()
        self.specials += [
            Instance("IBUFG", i_I=pads.ifclk, o_O=self.cd_usb.clk),
        ]

        self.specials += AsyncResetSynchronizer(self.cd_usb, ResetSignal())

        fifo = stream.AsyncFIFO([("data", 8)], 4)
        fifo = ClockDomainsRenamer({"write": "encoder", "read": "usb"})(fifo)
        self.submodules.fifo = fifo
        self.comb += Record.connect(sink, fifo.sink)

        self.specials += Instance("fx2_jpeg_streamer",
            # clk, rst
            i_rst=ResetSignal("usb"),
            i_clk=ClockSignal("usb"),

            # jpeg encoder interface
            i_sink_stb=fifo.source.valid,
            i_sink_data=fifo.source.data,
            o_sink_ack=fifo.source.ready,

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

        # add vhdl sources
        platform.add_source_dir(os.path.join("gateware", "streamer", "vhdl"))
