# ycbcr422to444

from litex.gen import *
from litex.soc.interconnect.stream import *

from gateware.csc.common import *

datapath_latency = 2

@CEInserter()
class YCbCr422to444Datapath(Module):
    """YCbCr 422 to 444

      Input:                    Output:
        Y0    Y1    Y2   Y3       Y0     Y1   Y2   Y3
      Cb01  Cr01  Cb23 Cr23  --> Cb01  Cb01 Cb23 Cb23
                                 Cr01  Cr01 Cr23 Cr23
    """
    latency = 2
    def __init__(self, dw):
        self.sink = sink = Record(ycbcr422_layout(dw))
        self.source = source = Record(ycbcr444_layout(dw))
        self.last = Signal()

        # # #

        # delay ycbcr signals
        ycbcr_delayed = [sink]
        for i in range(self.latency):
            ycbcr_n = Record(ycbcr422_layout(dw))
            for name in ["y", "cb_cr"]:
                self.sync += getattr(ycbcr_n, name).eq(getattr(ycbcr_delayed[-1], name))
            ycbcr_delayed.append(ycbcr_n)

        # parity
        parity = Signal()
        self.sync += If(self.last, parity.eq(0)).Else(parity.eq(~parity))

        # output
        self.sync += [
            If(parity,
                self.source.y.eq(ycbcr_delayed[1].y),
                self.source.cb.eq(ycbcr_delayed[1].cb_cr),
                self.source.cr.eq(sink.cb_cr),
            ).Else(
                self.source.y.eq(ycbcr_delayed[1].y),
                self.source.cb.eq(ycbcr_delayed[2].cb_cr),
                self.source.cr.eq(ycbcr_delayed[1].cb_cr)
            )
        ]

class YCbCr422to444(PipelinedActor, Module):
    def __init__(self, dw=8):
        self.sink = sink = stream.Endpoint(EndpointDescription(ycbcr422_layout(dw)))
        self.source = source = stream.Endpoint(EndpointDescription(ycbcr444_layout(dw)))

        # # #

        self.submodules.datapath = YCbCr422to444Datapath(dw)
        PipelinedActor.__init__(self, self.datapath.latency)
        self.comb += [
            self.datapath.last.eq(sink.valid & sink.last),
            self.datapath.ce.eq(sink.valid & self.pipe_ce)
        ]
        for name in ["y", "cb_cr"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))
