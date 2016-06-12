#!/usr/bin/env python3

from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient("192.168.1.50", 1234, csr_data_width=8)
wb.open()

# # #

logic_analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)

cond = {}
logic_analyzer.configure_trigger(cond=cond)
logic_analyzer.run(offset=256, length=512)

while not logic_analyzer.done():
    pass
logic_analyzer.upload()

logic_analyzer.save("dump.vcd")

# # #

wb.close()
