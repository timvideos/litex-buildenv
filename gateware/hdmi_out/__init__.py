from litex.gen import *

from litex.soc.interconnect.csr import AutoCSR
from litex.soc.interconnect import dma_lasmi

from gateware.compat import *
from gateware.hdmi_out.format import bpp, pixel_layout, FrameInitiator, VTG
from gateware.hdmi_out.phy import Driver


class HDMIOut(Module, AutoCSR):
    def __init__(self, pads, lasmim, external_clocking=None):
        pack_factor = lasmim.dw//bpp

        g = DataFlowGraph()

        self.fi = FrameInitiator(lasmim.aw, pack_factor)

        intseq = IntSequence(lasmim.aw, lasmim.aw)
        dma_out = AbstractActor(stream.Buffer)
        g.add_connection(self.fi, intseq, source_subr=self.fi.dma_subr())
        g.add_pipeline(intseq, AbstractActor(stream.Buffer), dma_lasmi.Reader(lasmim), dma_out)

        cast = Cast(lasmim.dw, pixel_layout(pack_factor), reverse_to=True)
        vtg = VTG(pack_factor)
        self.driver = Driver(pack_factor, pads, external_clocking)

        g.add_connection(self.fi, vtg, source_subr=self.fi.timing_subr, sink_ep="timing")
        g.add_connection(dma_out, cast)
        g.add_connection(cast, vtg, sink_ep="pixels")
        g.add_connection(vtg, self.driver)
        self.submodules += CompositeActor(g)
