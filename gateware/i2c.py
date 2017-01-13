from litex.gen import *
from litex.gen.fhdl import *
from litex.gen.fhdl.specials import Tristate
from litex.soc.interconnect.csr import *


_TristateLayout = [("w", 1), ("oe", 1), ("r", 1)]
_I2CLayout = [("sda", _TristateLayout), ("scl", _TristateLayout)]


class I2C(Module, AutoCSR):
    def __init__(self, pads):
        self._w = CSRStorage(8, name="w", reset=1)
        self._r = CSRStatus(1, name="r")

        if isinstance(pads.sda, Signal):
            _sda_w = Signal()
            _sda_oe = Signal()
            _sda_r = Signal()
            self.comb +=[
                pads.scl.eq(self._w.storage[0]),
                _sda_oe.eq(self._w.storage[1]),
                _sda_w.eq(self._w.storage[2]),
                self._r.status[0].eq(_sda_r)
            ]
            self.specials += Tristate(pads.sda, _sda_w, _sda_oe, _sda_r)
        else:  
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
        self.i2c_pads = []

    def get_i2c_pads(self):
        i2c_pads = Record(_I2CLayout)
        self.i2c_pads.append(i2c_pads)
        return i2c_pads

    def finalize(self):
        t = Signal(max=len(self.i2c_pads))

        self.sel = CSRStorage(t.nbits)

        # internal signals
        scl_oe = Signal()
        scl_w = Signal()
        scl_r = Signal()

        sda_oe = Signal()
        sda_w = Signal()
        sda_r = Signal()

        # tristate
        self.specials += [
            Tristate(self.out_pads.scl, scl_w, scl_oe, scl_r),
            Tristate(self.out_pads.sda, sda_w, sda_oe, sda_r)
        ]

        cases = {}
        for i, pads in enumerate(self.i2c_pads):
            cases[i] = [
                scl_oe.eq(pads.scl.oe),
                scl_w.eq(pads.scl.w),
                pads.scl.r.eq(scl_r),
                
                sda_oe.eq(pads.sda.oe),
                sda_w.eq(pads.sda.w),
                pads.sda.r.eq(sda_r)
            ]
        self.comb += Case(self.sel.storage, cases)
