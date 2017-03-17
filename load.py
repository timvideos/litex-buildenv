#!/usr/bin/env python3

import sys
import os

cmd, prog = sys.argv[:2]
if len(sys.argv) == 3:
    fname = sys.argv[2]
else:
    p = os.environ['PLATFORM']
    t = os.environ['TARGET']
    c = os.environ['CPU']

    fname = "build/{p}_{t}_{c}/gateware/top.bit".format(
        p=p, t=t, c=c)

if prog == 'ise':
    from litex.build.xilinx import iMPACT
    prog = iMPACT()
elif prog == 'vivado':
    from litex.build.xilinx import VivadoProgrammer
    prog = VivadoProgrammer()
else:
    raise SystemError('Unknown programmer {}'.format(prog))

if not os.path.exists(fname):
    raise SystemError('File {} not found'.format(fname))

if not fname.endswith('.bit'):
    raise SystemError('Use the .bit file')

prog.load_bitstream(fname)
