#!/usr/bin/env python3

from IPython import embed

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

from common import *
from firmware.pattern import *


def main():
    args, wb = connect("LiteX Etherbone Interactive Console")
    print_memmap(wb)
    print()

    define = "#define PATTERN_FRAMEBUFFER_BASE "
    pattern_offset = 0
    for l in open("firmware/pattern.c").readlines():
        if not l.startswith(define):
            continue

        pattern_offset = eval(l[len(define):-1])
    assert pattern_offset != 0

    pattern_mem = wb.mems.main_ram.base + pattern_offset

    print()
    print("Pattern   Offset: 0x{:x}".format(pattern_offset))
    print("Pattern Location: 0x{:x}".format(pattern_mem))
    print()

    for i in range(0, 256):
        wb.write(pattern_mem+i*128, [0x801080ff]*128)

    try:
        embed()
    finally:
        wb.close()


if __name__ == "__main__":
    main()
