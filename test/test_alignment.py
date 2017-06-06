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

DVISAMPLER_TOO_LATE  = 0x1
DVISAMPLER_TOO_EARLY = 0x2

def configure_delay(channel, delay):
    if channel == 0:
        wb.regs.hdmi_in0_data0_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
        for i in range(delay):
            wb.regs.hdmi_in0_data0_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)
    elif channel == 1:
        wb.regs.hdmi_in0_data1_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
        for i in range(delay):
            wb.regs.hdmi_in0_data1_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)
    elif channel == 2:
        wb.regs.hdmi_in0_data2_cap_dly_ctl.write(DVISAMPLER_DELAY_RST)
        for i in range(delay):
            wb.regs.hdmi_in0_data2_cap_dly_ctl.write(DVISAMPLER_DELAY_INC)
    else:
        ValueError

def get_phase_status(channel, measure_time=1):
    phase_status = 0
    if channel == 0:
        wb.regs.hdmi_in0_data0_cap_phase_reset.write(1)
        time.sleep(measure_time)
        phase_status = (wb.regs.hdmi_in0_data0_cap_phase.read() & 0x3)
    elif channel == 1:
        wb.regs.hdmi_in0_data1_cap_phase_reset.write(1)
        time.sleep(measure_time)
        phase_status = (wb.regs.hdmi_in0_data1_cap_phase.read() & 0x3)
    elif channel == 2:
        wb.regs.hdmi_in0_data2_cap_phase_reset.write(1)
        time.sleep(measure_time)
        phase_status = (wb.regs.hdmi_in0_data2_cap_phase.read() & 0x3)
    else:
        ValueError

    return (phase_status == DVISAMPLER_TOO_LATE,
            phase_status == DVISAMPLER_TOO_EARLY)

for channel in range(3):
    for delay in range(32):
        configure_delay(channel, delay)
        too_late, too_early = get_phase_status(channel)
        print("CHAN: {:d} / DELAY: {:d} / TOO_LATE: {:d} / TOO_EARLY: {:d}".format(
            channel, delay, too_late, too_early))

# # #

wb.close()
