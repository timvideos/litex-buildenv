#!/usr/bin/env python3
import time

from litex.soc.tools.remote.comm_udp import CommUDP
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = CommUDP("192.168.1.50", 20000)
wb.open()

# # #

wb.regs.hdmi_in_clocking_mmcm_reset.write(1)
wb.regs.hdmi_in_clocking_mmcm_reset.write(0)

time.sleep(2)

logic_analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)

cond = {}
logic_analyzer.configure_trigger(cond=cond)
logic_analyzer.run(offset=256, length=2048)

while not logic_analyzer.done():
    pass
logic_analyzer.upload()

logic_analyzer.save("dump.vcd")

# # #

wb.close()
