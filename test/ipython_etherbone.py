#!/usr/bin/env python3

from IPython import embed

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

from common import *


def main():
    args, wb = connect("LiteX Etherbone Interactive Console")
    print_memmap(wb)
    print()

    analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", config_csv='{}/analyzer.csv'.format(make_testdir(args)), debug=True)

    try:
        embed()
    finally:
        wb.close()


if __name__ == "__main__":
    main()
