#!/usr/bin/env python3

from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient("192.168.1.50", 1234, csr_data_width=8, debug=False)
wb.open()

# # #

analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
analyzer.configure_trigger(cond={})
analyzer.configure_subsampler(1)
analyzer.run(offset=16, length=1024)
while not analyzer.done():
    pass
analyzer.upload()
analyzer.save("dump.vcd")

# # #

wb.close()
