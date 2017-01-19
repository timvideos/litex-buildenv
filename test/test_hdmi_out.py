import time

from litex.soc.tools.remote import RemoteClient

wb = RemoteClient(debug=True)
wb.open()
regs = wb.regs


def config_1080p60(bpp):
    write_mmcm_reg(0x8, 0x1000 + (2 << 6) + 3)
    write_mmcm_reg(0xa, 0x1000 + (1 << 6) + 1)

    regs.hdmi_out0_core_initiator_hres.write(1920)
    regs.hdmi_out0_core_initiator_hsync_start.write(1920+88)
    regs.hdmi_out0_core_initiator_hsync_end.write(1920+88+44)
    regs.hdmi_out0_core_initiator_hscan.write(2200)

    regs.hdmi_out0_core_initiator_vres.write(1080)
    regs.hdmi_out0_core_initiator_vsync_start.write(1080+4)
    regs.hdmi_out0_core_initiator_vsync_end.write(1080+4+5)
    regs.hdmi_out0_core_initiator_vscan.write(1125)

    regs.hdmi_out0_core_initiator_enable.write(0)
    regs.hdmi_out0_core_initiator_base.write(0)
    regs.hdmi_out0_core_initiator_length.write(1920*1080*bpp)
    regs.hdmi_out0_core_initiator_enable.write(1)


def config_720p60(bpp):
    write_mmcm_reg(0x8, 0x1000 + (4 << 6)  + 6)
    write_mmcm_reg(0xa, 0x1000 + (2  << 6) + 2)

    regs.hdmi_out0_core_initiator_hres.write(1280)
    regs.hdmi_out0_core_initiator_hsync_start.write(1390)
    regs.hdmi_out0_core_initiator_hsync_end.write(1430)
    regs.hdmi_out0_core_initiator_hscan.write(1650)

    regs.hdmi_out0_core_initiator_vres.write(720)
    regs.hdmi_out0_core_initiator_vsync_start.write(725)
    regs.hdmi_out0_core_initiator_vsync_end.write(730)
    regs.hdmi_out0_core_initiator_vscan.write(750)

    regs.hdmi_out0_core_initiator_enable.write(0)
    regs.hdmi_out0_core_initiator_base.write(0)
    regs.hdmi_out0_core_initiator_length.write(1280*720*bpp)
    regs.hdmi_out0_core_initiator_enable.write(1)

    #regs.hdmi_out0_core_initiator_base.write(0x02000000)
    #regs.hdmi_out0_core_initiator_length.write(1280*720*bpp)
    #time.sleep(1)
    #regs.hdmi_out0_core_initiator_enable.write(1)


def read_mmcm_reg(address):
    regs.hdmi_out0_driver_clocking_drp_addr.write(address)
    regs.hdmi_out0_driver_clocking_drp_dwe.write(0)
    regs.hdmi_out0_driver_clocking_drp_den.write(1)
    return regs.hdmi_out0_driver_clocking_drp_do.read()


def write_mmcm_reg(address, data):
    regs.hdmi_out0_driver_clocking_drp_addr.write(address)
    regs.hdmi_out0_driver_clocking_drp_di.write(data)
    regs.hdmi_out0_driver_clocking_drp_dwe.write(1)
    regs.hdmi_out0_driver_clocking_drp_den.write(1)


def read_mmcm_config():
    for i in range(32):
        print("%d : %04x" %(i, read_mmcm_reg(i)))

# # #

RGB_WHITE  = 0x00ffffff
RGB_YELLOW = 0x0000ffff
RGB_CYAN   = 0x00ffff00
RGB_GREEN  = 0x0000ff00
RGB_PURPLE = 0x00ff00ff
RGB_RED    = 0x000000ff
RGB_BLUE   = 0x00ff0000
RGB_BLACK  = 0x00000000

color_bar_rgb = [RGB_WHITE,
                 RGB_YELLOW,
                 RGB_CYAN,
                 RGB_GREEN,
                 RGB_PURPLE,
                 RGB_RED,
                 RGB_BLUE,
                 RGB_BLACK]

def draw_color_bar_rgb():
    for y in range(720):
        for x in range(1280):
            color = color_bar_rgb[(x*8)//1280]
            wb.write(wb.mems.main_ram.base + 4*(1280*y + x), color)


YCBCR422_WHITE  = 0x80ff80ff
YCBCR422_YELLOW = 0x00e194e1
YCBCR422_CYAN   = 0xabb200b2
YCBCR422_GREEN  = 0x2b951595
YCBCR422_PURPLE = 0xd469e969
YCBCR422_RED    = 0x544cff4c
YCBCR422_BLUE   = 0xff1d6f1d
YCBCR422_BLACK  = 0x80108010

color_bar_ycbcr422 = [YCBCR422_WHITE,
                      YCBCR422_YELLOW,
                      YCBCR422_CYAN,
                      YCBCR422_GREEN,
                      YCBCR422_PURPLE,
                      YCBCR422_RED,
                      YCBCR422_BLUE,
                      YCBCR422_BLACK]

def draw_color_bar_ycbcr422():
    for y in range(720):
        for x in range(1280):
            if x%2 == 0:
                color = color_bar_ycbcr422[(x*8)//1280]
                wb.write(wb.mems.main_ram.base + 4*(1280//2*y + x//2), color)

# # #

config_720p60(2)
draw_color_bar_ycbcr422()

# # #

wb.close()
