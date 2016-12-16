#!/usr/bin/env python3

from IPython import embed

from common import *


def main():
    wb = connect("LiteX Etherbone Interactive Console")
    print_memmap(wb)
    print()

    try:
        embed()
    finally:
        wb.close()


if __name__ == "__main__":
    main()
