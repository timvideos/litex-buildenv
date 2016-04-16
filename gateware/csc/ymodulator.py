# ymodulator

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.genlib.cdc import MultiReg
from migen.bank.description import *
from migen.flow.actor import *

from gateware.csc.common import *

datapath_latency = 1

@DecorateModule(InsertCE)
class YModulatorDatapath(Module):
    def __init__(self, dw, value):
        self.sink = sink = Record(ycbcr444_layout(dw))
        self.source = source = Record(ycbcr444_layout(dw))

        # # #

        y_modulated = Signal(2*dw)
        self.sync += y_modulated.eq(sink.y * value)
        self.sync += [
            source.cb.eq(sink.cb),
            source.cr.eq(sink.cr)
        ]
        self.comb += saturate(y_modulated[dw:], source.y , 16, 235)


class YModulator(PipelinedActor, Module, AutoCSR):
    def __init__(self, dw=8):
        self.sink = sink = Sink(EndpointDescription(ycbcr444_layout(dw), packetized=True))
        self.source = source = Source(EndpointDescription(ycbcr444_layout(dw), packetized=True))
        PipelinedActor.__init__(self, 1)
        self.latency = datapath_latency

        self._value = CSRStorage(dw)

        # # #

        value = Signal(dw)
        self.specials += MultiReg(self._value.storage, value)

        self.submodules.datapath = YModulatorDatapath(dw, value)
        self.comb += self.datapath.ce.eq(sink.stb & self.pipe_ce)
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))
