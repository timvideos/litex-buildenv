#!/usr/bin/env python3
from litex.build.xilinx import iMPACT

prog = iMPACT()
prog.load_bitstream("build/gateware/top.bit")
