import time

# DDR3 init and test for a7ddrphy design (skeleton)

dfii_control_sel     = 0x01
dfii_control_cke     = 0x02
dfii_control_odt     = 0x04
dfii_control_reset_n = 0x08

dfii_command_cs     = 0x01
dfii_command_we     = 0x02
dfii_command_cas    = 0x04
dfii_command_ras    = 0x08
dfii_command_wrdata = 0x10
dfii_command_rddata = 0x20

sdram_base = 0x40000000

def main(wb):
    wb.open()
    regs = wb.regs
    # # #

    # release reset
    regs.sdram_dfii_pi0_address.write(0x0)
    regs.sdram_dfii_pi0_baddress.write(0)
    regs.sdram_dfii_control.write(dfii_control_odt|dfii_control_reset_n)
    time.sleep(0.001)

    # bring cke high
    regs.sdram_dfii_pi0_address.write(0x0)
    regs.sdram_dfii_pi0_baddress.write(0)
    regs.sdram_dfii_control.write(dfii_control_cke|dfii_control_odt|dfii_control_reset_n)
    time.sleep(0.001)

    # load mode register 2
    regs.sdram_dfii_pi0_address.write(0x408)
    regs.sdram_dfii_pi0_baddress.write(2)
    regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
    regs.sdram_dfii_pi0_command_issue.write(1)

    # load mode register 3
    regs.sdram_dfii_pi0_address.write(0x0)
    regs.sdram_dfii_pi0_baddress.write(3)
    regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
    regs.sdram_dfii_pi0_command_issue.write(1)

    # load mode register 1
    regs.sdram_dfii_pi0_address.write(0x6);
    regs.sdram_dfii_pi0_baddress.write(1);
    regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
    regs.sdram_dfii_pi0_command_issue.write(1)

    # load mode register 0, cl=7, bl=8
    regs.sdram_dfii_pi0_address.write(0x930);
    regs.sdram_dfii_pi0_baddress.write(0);
    regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
    regs.sdram_dfii_pi0_command_issue.write(1)
    time.sleep(0.001)

    # zq calibration
    regs.sdram_dfii_pi0_address.write(0x400);
    regs.sdram_dfii_pi0_baddress.write(0);
    regs.sdram_dfii_pi0_command.write(dfii_command_we|dfii_command_cs)
    regs.sdram_dfii_pi0_command_issue.write(1)
    time.sleep(0.001)

    # enable write leveling
    if False:
        regs.sdram_dfii_pi0_address.write(0x6 | (1 << 7))
        regs.sdram_dfii_pi0_baddress.write(1)
        regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
        regs.sdram_dfii_pi0_command_issue.write(1)

    # enable read leveling
    if False:
        regs.sdram_dfii_pi0_address.write(0x4)
        regs.sdram_dfii_pi0_baddress.write(3)
        regs.sdram_dfii_pi0_command.write(dfii_command_ras|dfii_command_cas|dfii_command_we|dfii_command_cs)
        regs.sdram_dfii_pi0_command_issue.write(1)

    # hardware control
    regs.sdram_dfii_control.write(dfii_control_sel)

    def seed_to_data(seed, random=False):
        if random:
            return (1664525*seed + 1013904223) & 0xffffffff
        else:
            return seed

    # test memory
    for i in range(32):
        wb.write(sdram_base + 4*i, seed_to_data(i))
    for i in range(32):
        print("{:08x} / {:08x}".format(wb.read(sdram_base + 4*i), seed_to_data(i)))

    # # #
    wb.close()
