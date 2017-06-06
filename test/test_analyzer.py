#!/usr/bin/env python3
import time

from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient()
wb.open()

# # #

logic_analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)

logic_analyzer.configure_trigger(cond={"charsync0_data": 0x354})
logic_analyzer.run(offset=32, length=128)

while not logic_analyzer.done():
    pass
logic_analyzer.upload()

logic_analyzer.save("dump.vcd")

# # #

wb.close()
