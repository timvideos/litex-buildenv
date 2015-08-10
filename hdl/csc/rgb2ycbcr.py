# rgb2ycbcr

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *

from hdl.csc.common import *

# TODO:
# - see if we can regroup some stages without impacting timings (would reduce latency and registers).
# - test implementation
# - do more tests.


def rgb2ycbcr_coefs(dw, cw=None):
    return {
        "ca" : coef(0.1819, cw),
        "cb" : coef(0.0618, cw),
        "cc" : coef(0.6495, cw),
        "cd" : coef(0.5512, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax" : 2**dw-1,
        "cmax" : 2**dw-1,
        "ymin" : 0,
        "cmin" : 0
    }


datapath_latency = 8


@DecorateModule(InsertCE)
class RGB2YCbCrDatapath(Module):
    def __init__(self, rgb_w, ycbcr_w, coef_w):
        self.sink = sink = Record(rgb_layout(rgb_w))
        self.source = source = Record(ycbcr_layout(ycbcr_w))

        # # #

        coefs = rgb2ycbcr_coefs(ycbcr_w, coef_w)

        # delay rgb signals
        rgb_delayed = [sink]
        for i in range(datapath_latency):
            rgb_n = Record(rgb_layout(rgb_w))
            for name in ["r", "g", "b"]:
                self.sync += getattr(rgb_n, name).eq(getattr(rgb_delayed[-1], name))
            rgb_delayed.append(rgb_n)

        # Hardware implementation:
        # (Equation from XAPP930)
        #    y = ca*(r-g) + g + cb*(b-g) + yoffset
        #   cb = cc*(r-y) + coffset
        #   cr = cd*(b-y) + coffset

        # stage 1
        # (r-g) & (b-g)
        r_minus_g = Signal((rgb_w + 1, True))
        b_minus_g = Signal((rgb_w + 1, True))
        self.sync += [
            r_minus_g.eq(sink.r - sink.g),
            b_minus_g.eq(sink.b - sink.g)
        ]

        # stage 2
        # ca*(r-g) & cb*(b-g)
        ca_mult_rg = Signal((rgb_w + coef_w + 1, True))
        cb_mult_bg = Signal((rgb_w + coef_w + 1, True))
        self.sync += [
            ca_mult_rg.eq(r_minus_g * coefs["ca"]),
            cb_mult_bg.eq(b_minus_g * coefs["cb"])
        ]

        # stage 3
        # ca*(r-g) + cb*(b-g)
        carg_plus_cbbg = Signal((rgb_w + coef_w + 2, True))
        self.sync += [
            carg_plus_cbbg.eq(ca_mult_rg + cb_mult_bg)
        ]

        # stage 4
        # yraw = ca*(r-g) + cb*(b-g) + g
        yraw = Signal((rgb_w + 3, True))
        self.sync += [
            yraw.eq(carg_plus_cbbg[coef_w:] + rgb_delayed[3].g)
        ]

        # stage 5
        # r - yraw
        # b - yraw
        b_minus_yraw = Signal((rgb_w + 4, True))
        r_minus_yraw = Signal((rgb_w + 4, True))
        yraw_r0 = Signal((rgb_w + 3, True))
        self.sync += [
            b_minus_yraw.eq(rgb_delayed[4].b - yraw),
            r_minus_yraw.eq(rgb_delayed[4].r - yraw),
            yraw_r0.eq(yraw)
        ]

        # stage 6
        # cc*yraw
        # cd*yraw
        cc_mult_ryraw = Signal((rgb_w + coef_w + 4, True))
        cd_mult_byraw = Signal((rgb_w + coef_w + 4, True))
        yraw_r1 = Signal((rgb_w + 3, True))
        self.sync += [
            cc_mult_ryraw.eq(b_minus_yraw * coefs["cc"]),
            cd_mult_byraw.eq(r_minus_yraw * coefs["cd"]),
            yraw_r1.eq(yraw_r0)
        ]

        # stage 7
        # y = (yraw + yoffset)
        # cb = (cc*(r - yraw) + coffset)
        # cr = (cd*(b - yraw) + coffset)
        y = Signal((rgb_w + 3, True))
        cb = Signal((rgb_w + 4, True))
        cr = Signal((rgb_w + 4, True))
        self.sync += [
            y.eq(yraw_r1 + coefs["yoffset"]),
            cb.eq(cc_mult_ryraw[coef_w:] + coefs["coffset"]),
            cr.eq(cd_mult_byraw[coef_w:] + coefs["coffset"])
        ]

        # stage 8
        # saturate
        self.sync += [
            saturate(y, source.y, coefs["ymin"], coefs["ymax"]),
            saturate(cb, source.cb, coefs["cmin"], coefs["cmax"]),
            saturate(cr, source.cr, coefs["cmin"], coefs["cmax"])
        ]


class RGB2YCbCr(PipelinedActor, Module):
    def __init__(self, rgb_w=8, ycbcr_w=8, coef_w=8):
        self.sink = sink = Sink(EndpointDescription(rgb_layout(rgb_w), packetized=True))
        self.source = source = Source(EndpointDescription(ycbcr_layout(ycbcr_w), packetized=True))
        PipelinedActor.__init__(self, datapath_latency)

        # # #

        self.submodules.datapath = RGB2YCbCrDatapath(rgb_w, ycbcr_w, coef_w)
        self.comb += self.datapath.ce.eq(self.pipe_ce)
        for name in ["r", "g", "b"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))
