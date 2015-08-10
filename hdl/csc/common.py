from migen.fhdl.std import *


def saturate(i, o, minimum, maximum):
    return [
        If(i > maximum,
            o.eq(maximum)
        ).Elif(i < minimum,
            o.eq(minimum)
        ).Else(
            o.eq(i)
        )
    ]

def coef(value, cw=None):
    return int(value * 2**cw) if cw is not None else value


def sd_ntsc_coefs(dw, cw=None):
    return {
        "ca" : coef(0.2568, cw),
        "cb" : coef(0.0979, cw),
        "cc" : coef(0.5910, cw),
        "cd" : coef(0.5772, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax" : 235*2**(dw-8),
        "cmax" : 235*2**(dw-8),
        "ymin" : 2**dw-1,
        "cmin" : 2**dw-1
    }


def hd_pal_coefs(dw, cw=None):
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


def yuv_coefs(dw, cw=None):
    return {
        "ca" : coef(0.299, cw),
        "cb" : coef(0.114, cw),
        "cc" : coef(0.877283, cw),
        "cd" : coef(0.492111, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax" : 2**dw-1,
        "cmax" : 2**dw-1,
        "ymin" : 0,
        "cmin" : 0
    }


def rgb_layout(dw):
    return [("r", dw), ("g", dw), ("b", dw)]


def ycbcr_layout(dw):
    return [("y", dw), ("cb", dw), ("cr", dw)]
