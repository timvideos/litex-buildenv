# ycbcr2rgb

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *

from hdl.csc.common import *

def ycbcr2rgb_coefs(dw, cw=None):
    ca = 0.1819
    cb = 0.0618
    cc = 0.5512
    cd = 0.6495
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
        "acoef": coef(1/cd, cw),
        "bcoef": coef(-cb/(cc*(1-ca-cb)), cw),
        "ccoef": coef(-ca/(cd*(1-ca-cb)), cw),
        "dcoef": coef(1/cc, cw)
    }