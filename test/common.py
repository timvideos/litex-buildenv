
import argparse
import os
import sys

from litex.soc.tools.remote import RemoteClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from make import make_args, make_testdir


def connect(desc, *args, **kw):
    parser = argparse.ArgumentParser(description=desc)
    make_args(parser, *args, **kw)
    parser.add_argument("--ipaddress")
    args = parser.parse_args()

    if not args.ipaddress:
        args.ipaddress = "{}.50".format(args.iprange)

    print("Connecting to {}".format(args.ipaddress))
    wb = RemoteClient(args.ipaddress, 1234, csr_csv="{}/csr.csv".format(make_testdir(args)))
    wb.open()
    print("Device: {}".format(get_dna(wb)))

    return wb


def print_memmap(wb):
    print("Memory Map")
    print("-"*20)
    for n, mem in sorted(wb.mems.d.items(), key=lambda i: i[1].base):
        print("{:20} @ 0x{:08x} -- {: 12} kbytes".format(n, mem.base, int(mem.size/1024)))


def get_dna(wb):
    try:
        dna = wb.regs.dna_id.read()
        return ''.join(hex(dna).split('000000'))
    except KeyError:
        return 'Unknown'


def write_and_check(reg, value):
    reg.write(value)
    r = reg.read()
    assert r == value, "Wanted {}, got {}".format(value, r)


