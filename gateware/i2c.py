from migen import *
from migen.fhdl import *
from migen.fhdl.specials import TSTriple
from litex.soc.interconnect.csr import *


class I2CPads:
    def __init__(self):
        self.sda = TSTriple(1)
        self.sda.w = self.sda.o
        self.sda.r = self.sda.i
        self.scl = TSTriple(1)
        self.scl.w = self.scl.o
        self.scl.r = self.scl.i

    def get_tristate(self, pads):
        return [
            self.scl.get_tristate(pads.scl),
            self.sda.get_tristate(pads.sda),
        ]

    def connect(self, other_pads):
        return [
            self.scl.oe.eq(other_pads.scl.oe),
            self.scl.w.eq(other_pads.scl.w),
            other_pads.scl.r.eq(self.scl.r),

            self.sda.oe.eq(other_pads.sda.oe),
            self.sda.w.eq(other_pads.sda.w),
            other_pads.sda.r.eq(self.sda.r),
        ]


class I2C(Module, AutoCSR):
    def __init__(self, pads):
        self._w = CSRStorage(8, name="w", reset=1)
        self._r = CSRStatus(1, name="r")

        if not isinstance(pads, I2CPads):
            out_pads = pads
            pads = I2CPads()
            self.specials += pads.get_tristate(out_pads)

        self.comb += [
            pads.scl.oe.eq(1),
            pads.scl.w.eq(self._w.storage[0]),
        ]

        self.comb += [
            pads.sda.oe.eq(self._w.storage[1]),
            pads.sda.w.eq(self._w.storage[2]),
            self._r.status[0].eq(pads.sda.r)
        ]


class I2CMux(Module, AutoCSR):
    def __init__(self, pads):
        self.out_pads = pads
        self.in_pads = []

    def get_i2c_pads(self):
        self.in_pads.append(I2CPads())
        return self.in_pads[-1]

    def finalize(self):
        t = Signal(max=len(self.in_pads))

        self.sel = CSRStorage(t.nbits)

        out_pads = I2CPads()
        self.specials += out_pads.get_tristate(self.out_pads)

        # Mux the signals
        cases = {}
        for i, pads in enumerate(self.in_pads):
            cases[i] = out_pads.connect(pads)
        self.comb += Case(self.sel.storage, cases)
