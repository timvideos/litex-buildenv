#!/usr/bin/env python3

import time

from common import *


def main():
    wb = connect("LiteX Etherbone Memtest BIST", target='memtest')
    print_memmap(wb)
    print()

    main_ram = wb.mems.main_ram
    print("DDR at 0x{:x} -- {} Megabytes".format(main_ram.base, int(main_ram.size/(1024*1024))))

    # init
    print("Init")
    wb.regs.generator_reset.write(1)
    wb.regs.checker_reset.write(1)

    wb.regs.generator_reset.write(0)
    wb.regs.checker_reset.write(0)

    base = int(256e3)
    #length = int((main_ram.size-base)*8/16) # 64e6 == 64 megabytes
    length = int(1)

    # write
    print("Write")
    write_and_check(wb.regs.generator_base, base)
    write_and_check(wb.regs.generator_length, length)

    assert not wb.regs.generator_done.read()
    wb.regs.generator_start.write(1)
    print("Waiting", end='')
    while wb.regs.generator_done.read() == 0:
        print(".", end='', flush=True)
        time.sleep(0.1)
    print()

    # read
    print("Read")
    assert wb.regs.checker_err_count.read() == 0

    write_and_check(wb.regs.checker_base, base)
    write_and_check(wb.regs.checker_length, length)

    assert not wb.regs.checker_done.read()
    wb.regs.checker_start.write(1)
    print("Waiting", end='')
    while wb.regs.checker_done.read() == 0:
        print("Errors:", wb.regs.checker_err_count.read())
        time.sleep(0.1)
    print()

    errors = wb.regs.checker_err_count.read()
    if errors != 0:
        addr = wb.regs.checker_err_addr.read()
        expect = wb.regs.checker_err_expect.read()
        actual = wb.regs.checker_err_actual.read()
        print("Error @ {} - {:x} != {:x}".format(addr, expect, actual))

    assert errors == 0, errors

    print("Done!")

    wb.close()


if __name__ == "__main__":
    main()
