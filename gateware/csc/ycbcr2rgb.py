# ycbcr2rgb

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *

from gateware.csc.common import *

def ycbcr2rgb_coefs(dw, cw=None):
    ca = 0.1819
    cb = 0.0618
    cc = 0.6495
    cd = 0.5512
    xcoef_w = None if cw is None else cw-2
    return {
        "ca" : coef(ca, cw),
        "cb" : coef(cb, cw),
        "cc" : coef(cc, cw),
        "cd" : coef(cd, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax" : 2**dw-1,
        "cmax" : 2**dw-1,
        "ymin" : 0,
        "cmin" : 0,
        "acoef": coef(1/cd, xcoef_w),
        "bcoef": coef(-cb/(cc*(1-ca-cb)), xcoef_w),
        "ccoef": coef(-ca/(cd*(1-ca-cb)), xcoef_w),
        "dcoef": coef(1/cc, xcoef_w)
    }

datapath_latency = 4


@DecorateModule(InsertCE)
class YCbCr2RGBDatapath(Module):
    def __init__(self, ycbcr_w, rgb_w, coef_w):
        self.sink = sink = Record(ycbcr444_layout(ycbcr_w))
        self.source = source = Record(rgb_layout(rgb_w))

        # # #

        coefs = ycbcr2rgb_coefs(rgb_w, coef_w)

        # delay ycbcr signals
        ycbcr_delayed = [sink]
        for i in range(datapath_latency):
            ycbcr_n = Record(ycbcr444_layout(ycbcr_w))
            for name in ["y", "cb", "cr"]:
                self.sync += getattr(ycbcr_n, name).eq(getattr(ycbcr_delayed[-1], name))
            ycbcr_delayed.append(ycbcr_n)

        # Hardware implementation:
        # (Equation from XAPP931)
        #  r = y - yoffset + (cr - coffset)*acoef
        #  b = y - yoffset + (cb - coffset)*bcoef + (cr - coffset)*ccoef
        #  g = y - yoffset + (cb - coffset)*dcoef

        # stage 1
        # (cr - coffset) & (cr - coffset)
        cb_minus_coffset = Signal((ycbcr_w + 1, True))
        cr_minus_coffset = Signal((ycbcr_w + 1, True))
        self.sync += [
            cb_minus_coffset.eq(sink.cb - coefs["coffset"]),
            cr_minus_coffset.eq(sink.cr - coefs["coffset"])
        ]

        # stage 2
        # (y - yoffset)
        # (cr - coffset)*acoef
        # (cb - coffset)*bcoef
        # (cr - coffset)*ccoef
        # (cb - coffset)*dcoef
        y_minus_yoffset = Signal((ycbcr_w + 1, True))
        cr_minus_coffset_mult_acoef = Signal((ycbcr_w + coef_w + 4, True))
        cb_minus_coffset_mult_bcoef = Signal((ycbcr_w + coef_w + 4, True))
        cr_minus_coffset_mult_ccoef = Signal((ycbcr_w + coef_w + 4, True))
        cb_minus_coffset_mult_dcoef = Signal((ycbcr_w + coef_w + 4, True))
        self.sync += [
            y_minus_yoffset.eq(ycbcr_delayed[1].y - coefs["yoffset"]),
            cr_minus_coffset_mult_acoef.eq(cr_minus_coffset * coefs["acoef"]),
            cb_minus_coffset_mult_bcoef.eq(cb_minus_coffset * coefs["bcoef"]),
            cr_minus_coffset_mult_ccoef.eq(cr_minus_coffset * coefs["ccoef"]),
            cb_minus_coffset_mult_dcoef.eq(cb_minus_coffset * coefs["dcoef"])
        ]

        # stage 3
        # line addition for all component
        r = Signal((ycbcr_w + 4, True))
        g = Signal((ycbcr_w + 4, True))
        b = Signal((ycbcr_w + 4, True))
        self.sync += [
            r.eq(y_minus_yoffset + cr_minus_coffset_mult_acoef[coef_w-2:]),
            g.eq(y_minus_yoffset + cb_minus_coffset_mult_bcoef[coef_w-2:] + cr_minus_coffset_mult_ccoef[coef_w-2:]),
            b.eq(y_minus_yoffset + cb_minus_coffset_mult_dcoef[coef_w-2:])
        ]

        # stage 4
        # saturate
        self.sync += [
            saturate(r, source.r, 0, 2**rgb_w-1),
            saturate(g, source.g, 0, 2**rgb_w-1),
            saturate(b, source.b, 0, 2**rgb_w-1)
        ]


class YCbCr2RGB(PipelinedActor, Module):
    def __init__(self, ycbcr_w=8, rgb_w=8, coef_w=8):
        self.sink = sink = Sink(EndpointDescription(ycbcr444_layout(ycbcr_w), packetized=True))
        self.source = source = Source(EndpointDescription(rgb_layout(rgb_w), packetized=True))
        PipelinedActor.__init__(self, datapath_latency)
        self.latency = datapath_latency

        # # #

        self.submodules.datapath = YCbCr2RGBDatapath(ycbcr_w, rgb_w, coef_w)
        self.comb += self.datapath.ce.eq(self.pipe_ce)
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["r", "g", "b"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))
