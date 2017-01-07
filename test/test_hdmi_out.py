import time

from litex.soc.tools.remote import RemoteClient

wb = RemoteClient(debug=True)
wb.open()
regs = wb.regs

def config_720p60(bpp):
    regs.hdmi_out0_core_initiator_hres.write(1280)
    regs.hdmi_out0_core_initiator_hsync_start.write(1390)
    regs.hdmi_out0_core_initiator_hsync_end.write(1430)
    regs.hdmi_out0_core_initiator_hscan.write(1650)

    regs.hdmi_out0_core_initiator_vres.write(720)
    regs.hdmi_out0_core_initiator_vsync_start.write(725)
    regs.hdmi_out0_core_initiator_vsync_end.write(730)
    regs.hdmi_out0_core_initiator_vscan.write(750)

    regs.hdmi_out0_core_initiator_enable.write(0)
    regs.hdmi_out0_core_initiator_base.write(0x02000000)
    regs.hdmi_out0_core_initiator_length.write(1280*720*bpp)
    time.sleep(1)
    regs.hdmi_out0_core_initiator_enable.write(1)

# # #

config_720p60(2)

# # #

wb.close()
