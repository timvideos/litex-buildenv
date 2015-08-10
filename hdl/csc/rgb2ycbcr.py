#           rgb2ycbcr
# (XAPP930 migen implementation)

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *

from hdl.csc.common import *


datapath_latency = 7


@DecorateModule(InsertCE)
class RGB2YCbCrDatapath(Module):
    def __init__(self, rgb_w, ycbcr_w, coef_w, coefs):
        self.sink = sink = Record(rgb_layout(rgb_w))
        self.source = source = Record(ycbcr_layout(ycbcr_w))

        # # #

        # delay rgb signals
        rgb_delayed = [Sink(rgb_layout(rgb_w))]
        for i in range(datapath_latency):
            rgb_n = Record(rgb_layout(rgb_w))
            for name in ["r", "g", "b"]:
                self.comb += getattr(rgb_n, name).eq(getattr(rgb_delayed[-1], name))
            rgb_delayed.append(rgb_n)

        # Hardware implementation:
        #    y = ca*(r-g) + g + cb*(b-g) + yoffset
        #    cb = cc*(r-y) + coffset
        #    cr = cd*(b-y) + coffset

        # clk 0
        # (r-g) & (b-g)
        r_minus_g = Signal((rgb_w + 1, True))
        b_minus_g = Signal((rgb_w + 1, True))
        self.sync += [
            r_minus_g.eq(sink.r - sink.g),
            b_minus_g.eq(sink.b - sink.g)
        ]

        # clk 1
        # ca*(r-g) & cb*(b-g)
        ca_mult_rg = Signal((rgb_w + coef_w + 1, True))
        cb_mult_bg = Signal((rgb_w + coef_w + 1, True))
        self.sync += [
            ca_mult_rg.eq(r_minus_g * coefs["ca"]),
            cb_mult_bg.eq(b_minus_g * coefs["cb"])
        ]

        # clk 2
        # ca*(r-g) + cb*(b-g)
        carg_plus_cbbg = Signal((rgb_w + coef_w + 2, True))
        self.sync += [
            carg_plus_cbbg.eq(ca_mult_rg + cb_mult_bg)
        ]

        # clk 3
        # yraw = ca*(r-g) + cb*(b-g) + g
        yraw = Signal((rgb_w + 3, True))
        self.sync += [
            yraw.eq(carg_plus_cbbg[coef_w:] + rgb_delayed[2].g)
        ]

        # clk 4
        # r - yraw
        # b - yraw
        b_minus_yraw = Signal((rgb_w + 4, True))
        r_minus_yraw = Signal((rgb_w + 4, True))
        yraw_r0 = Signal((rgb_w + 3, True))
        self.sync += [
            b_minus_yraw.eq(rgb_delayed[3].b - yraw),
            r_minus_yraw.eq(rgb_delayed[3].r - yraw),
            yraw_r0.eq(yraw)
        ]

        # clk 5
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

        # clk 6
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

        # clk 7
        # saturate
        self.sync += [
            saturate(y, source.y, coefs["ymin"], coefs["ymax"]),
            saturate(cb, source.cb, coefs["cmin"], coefs["cmax"]),
            saturate(cr, source.cr, coefs["cmin"], coefs["cmax"])
        ]


class RGB2YCbCr(PipelinedActor, Module):
    def __init__(self, rgb_w=8, ycbcr_w=8, coef_w=8, mode="HD"):
        self.sink = sink = Sink(rgb_layout(rgb_w))
        self.source = source = Source(ycbcr_layout(ycbcr_w))
        PipelinedActor.__init__(self, datapath_latency)

        # # #

        if mode in ["SD", "NTSC"]:
            coefs = sd_ntsc_coefs(ycbcr_w, coef_w)
        elif mode in ["HD", "PAL"]:
            coefs = hd_pal_coefs(ycbcr_w, coef_w)
        elif mode in ["YUV"]:
            coefs = yuv_coefs(ycbcr_w, coef_w)
        else:
            ValueError

        # datapath
        self.submodules.datapath = RGB2YCbCrDatapath(rgb_w, ycbcr_w, coef_w, coefs)
        self.comb += self.datapath.ce.eq(self.pipe_ce)
        for name in ["r", "g", "b"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))
