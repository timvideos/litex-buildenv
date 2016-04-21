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


def read_mmcm_reg(address):
    regs.clocking_drp_addr.write(address)
    regs.clocking_drp_dwe.write(0)
    regs.clocking_drp_den.write(1)
    return regs.clocking_drp_do.read()

def write_mmcm_reg(address, data):
    regs.clocking_drp_addr.write(address)
    regs.clocking_drp_di.write(data)
    regs.clocking_drp_dwe.write(1)
    regs.clocking_drp_den.write(1)

def read_mmcm_config():
    for i in range(32):
        print("%d : %04x" %(i, read_mmcm_reg(i)))


read_mmcm_config()
clkreg1 = read_mmcm_reg(0x8)
print("0x%04x, high: %d, low: %d" %(clkreg1, (clkreg1 >> 6) & (2**6-1), clkreg1 & (2**6-1)))
clkreg1 = read_mmcm_reg(0xa)
print("0x%04x, high: %d, low: %d" %(clkreg1, (clkreg1 >> 6) & (2**6-1), clkreg1 & (2**6-1)))

write_mmcm_reg(0x8, 0x1000 + (10 << 6) + 10)
write_mmcm_reg(0xa, 0x1000 +  (2 << 6) +  2)


# # #

wb.close()
