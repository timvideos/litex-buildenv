from litex.soc.tools.remote import RemoteClient

wb = RemoteClient("192.168.1.50", 1234, csr_data_width=8)
wb.open()
regs = wb.regs

# # #

regs.initiator_hres.write(1280)
regs.initiator_hsync_start.write(1390)
regs.initiator_hsync_end.write(1430)
regs.initiator_hscan.write(1650)

regs.initiator_vres.write(720)
regs.initiator_vsync_start.write(725)
regs.initiator_vsync_end.write(730)
regs.initiator_vscan.write(750)

regs.initiator_enable.write(1)

# # #

wb.close()
