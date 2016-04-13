#!/usr/bin/env python3

import time
import sys
sys.path.append("../")

from litex.soc.tools.remote import RemoteClient

wb = RemoteClient("192.168.1.50", 1234)
wb.open()

# # #

# test uart
for c in "hello world from host\n":
    wb.regs.uart_rxtx.write(ord(c))

# # #

wb.close()
