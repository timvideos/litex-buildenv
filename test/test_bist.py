#!/usr/bin/env python3
from litex.soc.tools.remote import RemoteClient

wb = RemoteClient(csr_data_width=8)
wb.open()
regs = wb.regs

# # #

test_size = 128*1024*1024

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

# # #

wb.close()
