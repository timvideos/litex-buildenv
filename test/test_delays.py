#!/usr/bin/env python3
import time

from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient()
wb.open()

# # #

DVISAMPLER_DELAY_RST = 0x1
DVISAMPLER_DELAY_INC = 0x2
DVISAMPLER_DELAY_DEC = 0x4

data0_delay = 0
data1_delay = 0
data2_delay = 1

wb.regs.hdmi_in0_data0_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
for i in range(data0_delay):
	wb.regs.hdmi_in0_data0_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)

wb.regs.hdmi_in0_data1_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
for i in range(data1_delay):
	wb.regs.hdmi_in0_data1_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)

wb.regs.hdmi_in0_data2_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
for i in range(data2_delay):
	wb.regs.hdmi_in0_data2_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)


# # #

wb.close()
