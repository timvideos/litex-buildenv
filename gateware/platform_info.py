from migen.fhdl.std import *
from migen.bank.description import *

def binify(s, size):
    assert size % 8 == 0
    blen = int(size / 8)
    assert len(s) <= blen
    s = s+'\0'*(blen-len(s))
    return sum(ord(c) << i * 8 for i, c in enumerate(reversed(s)))


class PlatformInfo(Module, AutoCSR):
    def __init__(self, platform, target):
        self.platform = CSRStatus(64)
        self.target = CSRStatus(64)

        self.comb += [
            self.platform.status.eq(binify(platform, 64)),
            self.target.status.eq(binify(target, 64)),
        ]
