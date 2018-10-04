import os
import struct

from migen import *
from litex.soc.interconnect import wishbone


class MemoryMustHaveContents(Memory):
    def load_init_data(self):
        assert os.path.exists(self.filename), (
            "ROM contents not found! {}".format(self.filename))

        data = []
        with open(self.filename, "rb") as firmware_file:
            while True:
                w = firmware_file.read(4)
                if not w:
                    break
                data.append(struct.unpack(">I", w)[0])
        data_size = len(data)*4
        assert data_size > 0
        assert data_size < self.size, (
            "Firmware is too big! {} bytes > {} bytes".format(
                data_size, self.size))
        print("Firmware {} bytes ({} bytes left)".format(
            data_size, self.size-data_size))

        self.init = data

    @staticmethod
    def emit_verilog(memory, ns, add_data_file):
        memory.load_init_data()
        return Memory.emit_verilog(memory, ns, add_data_file)


class FirmwareROM(wishbone.SRAM):
    def __init__(self, size, filename):
        wishbone.SRAM.__init__(self, size)

        # Switch the rom memory class to be able to lazy load contents.
        self.mem.__class__ = MemoryMustHaveContents
        self.mem.filename = filename
        self.mem.size = size
