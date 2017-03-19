#!/usr/bin/env python3
import time
from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient(debug=False)
wb.open()
regs = wb.regs

analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=False)

# # #

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

regs.sdram_dfii_control.write(0)

# release reset
regs.sdram_dfii_pi0_address.write(0x0)
regs.sdram_dfii_pi0_baddress.write(0)
regs.sdram_dfii_control.write(dfii_control_odt|dfii_control_reset_n)
time.sleep(0.1)

# bring cke high
regs.sdram_dfii_pi0_address.write(0x0)
regs.sdram_dfii_pi0_baddress.write(0)
regs.sdram_dfii_control.write(dfii_control_cke|dfii_control_odt|dfii_control_reset_n)
time.sleep(0.1)

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
time.sleep(0.1)

# zq calibration
regs.sdram_dfii_pi0_address.write(0x400);
regs.sdram_dfii_pi0_baddress.write(0);
regs.sdram_dfii_pi0_command.write(dfii_command_we|dfii_command_cs)
regs.sdram_dfii_pi0_command_issue.write(1)
time.sleep(0.1)

# hardware control
regs.sdram_dfii_control.write(dfii_control_sel)


# configure working bitslips and delays
bitslip = 2
delay = 6
for k in range(2):
    regs.ddrphy_dly_sel.write(1<<k)
    regs.ddrphy_rdly_dq_rst.write(1)
    for i in range(bitslip):
        # 7-series SERDES in DDR mode needs 3 pulses for 1 bitslip
        for j in range(3):
            regs.ddrphy_rdly_dq_bitslip.write(1)
    for i in range(delay):
        regs.ddrphy_rdly_dq_inc.write(1)

#

test_size = 1024*1024
run_analyzer = True

#

analyzer.configure_trigger(cond={"generator_start_re": 1})
analyzer.configure_trigger(cond={"checker_start_re": 1})
analyzer.configure_subsampler(1)
analyzer.run(offset=16, length=512)

regs.generator_reset.write(1)
regs.generator_reset.write(0)
regs.generator_base.write(0)
regs.generator_length.write((test_size*8)//128)

regs.generator_start.write(1)
while(not regs.generator_done.read()):
    pass

regs.checker_reset.write(1)
regs.checker_reset.write(0)
regs.checker_base.write(0)
regs.checker_length.write((test_size*8)//128)

regs.checker_start.write(1)
while(not regs.checker_done.read()):
    pass

print("errors: {:d}".format(regs.checker_err_count.read()))

if run_analyzer:
    while not analyzer.done():
        pass
    analyzer.upload()
    analyzer.save("dump.vcd")

# # #

wb.close()
