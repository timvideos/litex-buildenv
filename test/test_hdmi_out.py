from litex.soc.tools.remote import RemoteClient

wb = RemoteClient("192.168.1.50", 1234, csr_data_width=8)
wb.open()
regs = wb.regs


def config_1080p60():
    write_mmcm_reg(0x8, 0x1000 + (2 << 6) + 3)
    write_mmcm_reg(0xa, 0x1000 + (1 << 6) + 1)

    regs.initiator_hres.write(1920)
    regs.initiator_hsync_start.write(1920+88)
    regs.initiator_hsync_end.write(1920+88+44)
    regs.initiator_hscan.write(2200)

    regs.initiator_vres.write(1080)
    regs.initiator_vsync_start.write(1080+4)
    regs.initiator_vsync_end.write(1080+4+5)
    regs.initiator_vscan.write(1125)

    regs.initiator_enable.write(1)


def config_720p60():
    write_mmcm_reg(0x8, 0x1000 + (4 << 6)  + 6)
    write_mmcm_reg(0xa, 0x1000 + (2  << 6) + 2)

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


# # #

config_1080p60()
config_720p60()

# # #

wb.close()
