#!/usr/bin/env python3
import time
from litex.soc.tools.remote import RemoteClient
from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient(csr_data_width=8, debug=True)
wb.open()
regs = wb.regs

analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)

# # #

test_size = 64*1024*1024

analyzer.configure_trigger(cond={"generator_crossbar_port_cmd_valid": 1})
analyzer.configure_trigger(cond={"checker_crossbar_port_cmd_valid": 1})
analyzer.configure_subsampler(8)
analyzer.run(offset=16, length=256)

regs.generator_reset.write(1)
regs.generator_reset.write(0)
regs.generator_base.write(0)
regs.generator_length.write((test_size*8)//128)

regs.generator_shoot.write(1)
while(not regs.generator_done.read()):
    pass

regs.checker_reset.write(1)
regs.checker_reset.write(0)
regs.checker_base.write(0)
regs.checker_length.write((test_size*8)//128)

regs.checker_shoot.write(1)
while(not regs.checker_done.read()):
    pass

print("errors: {:d}".format(regs.checker_error_count.read()))

while not analyzer.done():
    pass
analyzer.upload()
analyzer.save("dump.vcd")

# # #

wb.close()
