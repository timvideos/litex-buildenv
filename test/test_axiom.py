#!/usr/bin/env python3

from collections import namedtuple


from IPython import embed

from common import *

from platforms import tofe_axiom


_LVDSPair = namedtuple("LVDSPair", ("p", "n"))
class LVDSPair(_LVDSPair):
    def set(self):
        for i in self:
            i.set()

    def clear(self):
        for i in self:
            i.clear()


class PinList(list):
    def set(self):
        for i in self:
            i.set()

    def clear(self):
        for i in self:
            i.clear()


class Pin:
    def __init__(self, name, reg, pos):
        self.name = name
        self._mask = 2**pos
        self._reg = reg

    def set(self):
        self._reg.write(self._reg.read() | self._mask)

    def clear(self):
        self._reg.write(self._reg.read() & ~self._mask)

    def __repr__(self):
        return "<Pin({}, {}>".format(self.name, int(bool(self._reg.read() & ~self._mask)))


class AxiomIO:

    def __init__(self, name, wb):
        self.name = name

        self.pins = PinList()

        self.io = {}
        self.lvds_p = {}
        self.lvds_n = {}

        for desc, pin in tofe_axiom._tofe_axiom[name].items():
            #diff_clk_a1n
            _, t, p = pin.split('_')
            l, n, v = p[0], int('0'+p[1:-1]), p[-1]

            if l == 'y':
                l, n = 'x', 1
            elif l == 'z':
                l, n = 'x', 2

            reg_name = "gpio_{}_{}_{}".format(t, l, v)

            pino = Pin(desc, getattr(wb.regs, reg_name), n)
            self.pins.append(pino)
            setattr(self, desc, pino)

            if desc.startswith('io'):
                self.io[int(desc[2:])] = pino

            if desc.startswith('lvds_'):
                n, v = int(desc[5:-1]), desc[-1]
                getattr(self, "lvds_{}".format(v))[n] = pino

        self.io = PinList([b for a, b in sorted(self.io.items())])
        self.lvds_p = PinList([b for a, b in sorted(self.lvds_p.items())])
        self.lvds_n = PinList([b for a, b in sorted(self.lvds_n.items())])

        self.lvds = PinList(LVDSPair(*i) for i in zip(self.lvds_p, self.lvds_n))

    def set(self, name):
        if name == 'all':
            for p in self.pins:
                p.set()
        else:
            getattr(self, name).set()
            
    def clear(self, name):
        if name == 'all':
            for p in self.pins:
                p.clear()
        else:
            getattr(self, name).clear()


class Pmod3:

    def _setup(self, l, name, anorth, asouth):
        for name, (a, b) in sorted(tofe_axiom._axiom_3pmod[name].items()):
            if a == 'north':
                a = anorth
            elif a == 'south':
                a = asouth
            else:
                assert False

            l.append(getattr(a, b))

    def __init__(self, anorth, asouth):
        self.nled = anorth.io
        self.sled = asouth.io

        self.north = PinList()
        self._setup(self.north, 'pnorth', anorth, asouth)
        self.middle = PinList()
        self._setup(self.middle, 'pmiddle', anorth, asouth)
        self.south = PinList()
        self._setup(self.south, 'psouth', anorth, asouth)


def main():
    args, wb = connect("LiteX Etherbone Interactive Console")
    print_memmap(wb)

    anorth = AxiomIO('north', wb)
    asouth = AxiomIO('south', wb)

    pmod3 = Pmod3(anorth, asouth)

    try:
        embed()
    finally:
        wb.close()



if __name__ == "__main__":
    main()
