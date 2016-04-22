import os
import struct

from litex.gen import *
from litex.soc.interconnect import wishbone


class FirmwareROM(wishbone.SRAM):
    def __init__(self, size, filename):
        if os.path.exists(filename):
            data = []
            with open(filename, "rb") as firmware_file:
                while True:
                    w = firmware_file.read(4)
                    if not w:
                        break
                    data.append(struct.unpack(">I", w)[0])
            data_size = len(data)*4
            assert data_size > 0
            assert data_size < size, (
                "firmware is too big: {}/{} bytes".format(
                    data_size, size))
            wishbone.SRAM.__init__(self, size, init=data)
        else:
            print("no firmware found, won't work on hardware".format(
                filename))
            wishbone.SRAM.__init__(self, size)
