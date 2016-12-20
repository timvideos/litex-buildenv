#!/usr/bin/env python3

import time
from collections import namedtuple

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

from common import *

MemError = namedtuple("MemError", ("address", "expected", "actual"))


def main():
    args, wb = connect("LiteX Etherbone Memtest BIST", target='memtest')
    print_memmap(wb)
    print()

    main_ram = wb.mems.main_ram
    print("DDR at 0x{:x} -- {} Megabytes".format(main_ram.base, int(main_ram.size/(1024*1024))))
    print()
    # init
    print("Reset")
    wb.regs.generator_reset.write(1)
    wb.regs.checker_reset.write(1)

    wb.regs.generator_reset.write(0)
    wb.regs.checker_reset.write(0)

    assert not wb.regs.checker_scope_error.read()
    print()

    analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", config_csv='{}/analyzer.csv'.format(make_testdir(args)), debug=True)
    print("Init analyzer")
    #analyzer.configure_trigger(cond={'checker_core_data_error': 1})
    analyzer.configure_trigger(cond={'data_error': 1})
    analyzer.configure_trigger(cond={})
    analyzer.configure_subsampler(1)
    analyzer.run(offset=16, length=1024)
    assert not analyzer.done()
    print()

    base = int(512e3)
    #length = int((main_ram.size-base)*8/16) # 64e6 == 64 megabytes
    #length = int(2e6)
    length = int(1)

    # write
    print("Write")
    write_and_check(wb.regs.generator_base, base)
    write_and_check(wb.regs.generator_length, length)

    assert not wb.regs.generator_done.read()
    wb.regs.generator_start.write(1)
    print("Waiting", end=' ')
    while wb.regs.generator_done.read() == 0:
        print(".", end='', flush=True)
        time.sleep(0.1)
    assert wb.regs.generator_done.read() == 1
    print()

    # read
    assert wb.regs.checker_err_count.read() == 0

    print("Read")
    write_and_check(wb.regs.checker_base, base)
    write_and_check(wb.regs.checker_length, length)

    assert not wb.regs.checker_done.read()
    assert not analyzer.done()
    wb.regs.checker_start.write(1)
    print("Waiting")
    while wb.regs.checker_done.read() == 0:
        print("  Errors:", wb.regs.checker_err_count.read())
        time.sleep(0.1)
    assert wb.regs.checker_done.read() == 1
    print("Final errors:", wb.regs.checker_err_count.read())

    errors = wb.regs.checker_err_count.read()

    if errors != 0:
        # Check litescope
        assert analyzer.done()
        analyzer.upload()
        analyzer.save('sim.vcd')

        data = {v.name: v for v in analyzer.dump().variables}

        okay = set()
        errors = {}
        for i in range(0, len(data['clk'].values)):
            address = hex(data['data_address'].values[i])

            if data['data_error'].values[i] != 1:
                okay.add(address)
                continue

            expected = data['data_expected'].values[i]
            actual = data['data_actual'].values[i]

            r = MemError(address, hex(expected), hex(actual))
            if address in errors:
                assert errors[address] == r
            else:
                errors[address] = r

        import pprint
        print(len(errors))
        pprint.pprint(errors)

        from IPython import embed
        embed()
        #print("Error @ {} - {:x} != {:x}".format(addr, expect, actual))

    print("Done!")

    wb.close()


if __name__ == "__main__":
    main()
