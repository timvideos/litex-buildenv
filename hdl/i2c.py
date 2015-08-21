from migen.fhdl.std import *
from migen.fhdl.specials import Tristate
from migen.bank.description import *


class I2C(Module, AutoCSR):
    def __init__(self, pads):
        self._w = CSRStorage(8, name="w")
        self._r = CSRStatus(1, name="r")

    # # #

        _sda_w = Signal()
        _sda_oe = Signal()
        _sda_r = Signal()
        self.comb +=[
            pads.scl.eq(self._w.storage[0]),
            _sda_oe.eq(self._w.storage[1]),
            _sda_w.eq(self._w.storage[2]),
            self._r.status[0].eq(_sda_r)
        ]
        self.specials +=Tristate(pads.sda, _sda_w, _sda_oe, _sda_r)
