#!/usr/bin/env python3

from IPython import embed

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

from common import *


def main():
    args, wb = connect("LiteX Etherbone Interactive Console")
    print_memmap(wb)
    print()

    analyzer_csv = '{}/analyzer.csv'.format(make_testdir(args))
    if os.path.exists(analyzer_csv):
        analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", config_csv=analyzer_csv, debug=True)
    else:
        print("WARNING: No litescope csv found at {},\nAssuming litescope not included in design!".format(analyzer_csv))

    try:
        embed()
    finally:
        wb.close()


if __name__ == "__main__":
    main()
