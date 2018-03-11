import os
import struct

from migen import *
from litex.soc.interconnect import wishbone


class MemoryMustHaveContents(Memory):
    @staticmethod
    def emit_verilog(memory, ns, add_data_file):
        assert memory.init, "ROM contents not found! {}".format(memory.filename)
        return Memory.emit_verilog(memory, ns, add_data_file)


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
                "Firmware is too big! {} bytes > {} bytes".format(
                    data_size, size))
            print("Firmware {} bytes ({} bytes left)".format(
                data_size, size-data_size))
            wishbone.SRAM.__init__(self, size, init=data)
        else:
            print("No firmware found! ({}) Won't compile.".format(
                filename))
            wishbone.SRAM.__init__(self, size)

        self.mem.__class__ = MemoryMustHaveContents
        self.mem.filename = filename
