#!/usr/bin/env python3

if False:
    from litex.build.xilinx import iMPACT
    prog = iMPACT()
else:
    from litex.build.xilinx import VivadoProgrammer
    prog = VivadoProgrammer()

prog.load_bitstream("build/gateware/top.bit")
