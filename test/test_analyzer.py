#!/usr/bin/env python3

from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient(debug=False, csr_data_width=8)
wb.open()

# # #

logic_analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)

cond = {}
logic_analyzer.configure_trigger(cond=cond)
logic_analyzer.run(offset=32, length=2048)

while not logic_analyzer.done():
    pass
logic_analyzer.upload()

logic_analyzer.save("dump.vcd")

print("%08x" %wb.regs.hdmi_out0_core_initiator_base.read())
print("%08x" %wb.regs.hdmi_out0_core_initiator_length.read())

# # #

wb.close()
