
import argparse
import os
import sys
import threading

from litex.soc.tools.remote import RemoteServer
from litex.soc.tools.remote import RemoteClient
from litex.soc.tools.remote import CommUART

TOP_DIR=os.path.join(os.path.dirname(__file__), "..")

sys.path.append(TOP_DIR)
from make import get_args, get_testdir


class ServerProxy(threading.Thread):
    daemon = True

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.ready = False

    def run(self):
        print("Starting proxy to {}".format(self.port))
        self.comm = CommUART(self.port, 115200)
        self.server = RemoteServer(self.comm)
        self.server.open()
        self.server.start()
        self.ready = True


def connect(desc, *args, add_args=None, **kw):
    parser = argparse.ArgumentParser(description=desc)
    get_args(parser, *args, **kw)
    parser.add_argument("--ipaddress")
    parser.add_argument("--port") #, desc="Serial port")
    if add_args is not None:
        add_args(parser)
    args = parser.parse_args()

    if args.port:
        s = ServerProxy(args.port)
        s.start()
        while not s.ready:
            continue

        args.ipaddress = "127.0.0.1"

    elif not args.ipaddress:
        args.ipaddress = "{}.50".format(args.iprange)

    print("Connecting to {}".format(args.ipaddress))
    test_dir = os.path.join(TOP_DIR, get_testdir(args))
    wb = RemoteClient(args.ipaddress, 1234, csr_csv="{}/csr.csv".format(test_dir))
    wb.open()
    print()
    print("Device DNA: {}".format(get_dna(wb)))
    print("   Git Rev: {}".format(get_git(wb)))
    print("  Platform: {}".format(get_platform(wb)))
    print("  Analyzer: {}".format(["No", "Yes"][hasattr(wb.regs, "analyzer")]))
    print("      XADC: {}".format(get_xadc(wb)))
    print()

    return args, wb


def print_memmap(wb):
    print("Memory Map")
    print("-"*20)
    for n, mem in sorted(wb.mems.d.items(), key=lambda i: i[1].base):
        mb = mem.size/1024/1024
        if mb > 1.0:
            extra_str = " ({:4} Mbytes)".format(int(mb))
        else:
            extra_str = ""
        print("{:20} @ 0x{:08x} -- {: 12} kbytes {}".format(n, mem.base, int(mem.size/1024), extra_str))


def get_dna(wb):
    try:
        dna = wb.regs.info_dna_id.read()
        return hex(dna)
    except (KeyError, AttributeError) as e:
        return 'Unknown'


def get_git(wb):
    try:
        commit = wb.regs.info_git_commit.read()
        return hex(commit)[2:]
    except (KeyError, AttributeError) as e:
        return 'Unknown'


# xadc stuff
def xadc2volts(v):
    return (v/4096.0*3)

def xadc2c(v):
    return (v*503.975/4096 - 273.15)

def get_xadc(wb):
    try:
        temp = xadc2c(wb.regs.xadc_temperature.read())
        vccaux = xadc2volts(wb.regs.xadc_vccaux.read())
        vccbram = xadc2volts(wb.regs.xadc_vccbram.read())
        vccint = xadc2volts(wb.regs.xadc_vccint.read())
        return "{:.1f}°C -- vccint: {:.2f}V  vccaux: {:.2f}V  vccbram: {:.2f}V".format(
            temp, vccaux, vccbram, vccint)
    except (KeyError, AttributeError) as e:
        return 'Unknown'


def stringify(reg):
    d = reg.read()
    chars = []
    for i in range(0, reg.length):
        b = (d >> (8 * i)) & 0xff
        if b > 0:
            chars.append(chr(b))
    chars.reverse()
    return ''.join(chars)


def get_platform(wb):
    try:
        target = stringify(wb.regs.info_platform_target)
        platform = stringify(wb.regs.info_platform_platform)
        return "{} on {}".format(target, platform)
    except (KeyError, AttributeError) as e:
        return 'Unknown on Unknown'


def write_and_check(reg, value):
    reg.write(value)
    r = reg.read()
    assert r == value, "Wanted {}, got {}".format(value, r)


def memdump(wb, start, length):
    data = wb.read(start, length)
    for i, d in enumerate(data):
        address = i*4 + start
        if address % 32 == 0:
            print()
            print("0x{:04x} ".format(address), sep=' ', end='')
        for b in struct.pack('>I', d):
            print("{:02x}".format(b), end=' ')


import struct

BLOCK_SIZE=64
def cmpflash(wb, start, filename, skip=0, max=1024):
    assert skip%4==0
    with open(filename, 'rb') as f:
        local_data=f.read()[:skip+max]
    j = skip
    while j < len(local_data):
        mem_data_len = min(BLOCK_SIZE, len(local_data)-j)
        mem_data = b"".join(struct.pack('>I', k) for k in wb.read(start+j, mem_data_len))
        for i in range(0, mem_data_len):
            addr, expected, actual = j+i+start, local_data[j+i], mem_data[i]
            if addr % 8 == 0:
                print()
                print("0x{:08x} ".format(addr), sep=' ', end='')
            if expected != actual:
                print()
                print("{:08x} {:02x} != {:02x}".format(addr, expected, actual))
            else:
                print(".", end="", flush=True)
        j += BLOCK_SIZE

