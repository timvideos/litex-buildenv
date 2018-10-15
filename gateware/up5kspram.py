from migen import *
from litex.soc.interconnect import wishbone

# ICE40 UltraPlus family-specific Wishbone interface to the Single Port RAM
# (SPRAM) primitives. Because SPRAM is much more coarse grained than Block
# RAM resources, this RAM is not configurable (at present, 64kB). Because
# it is single port, this module is meant to be used as the CPU's RAM region,
# leaving block RAM free for other use.

class Up5kSPRAM(Module):
    def __init__(self):
        self.bus = wishbone.Interface(32)

        bytesels = []
        for i in range(0, 2):
            datain = Signal(16)
            dataout = Signal(16)
            maskwren = Signal(4)
            wren = Signal(1)

            for j in range(16):
                self.comb += [self.bus.dat_r[16*i + j].eq(dataout[j])]

            self.comb += [
                datain.eq(self.bus.dat_w[16*i:16*i+16]),
                maskwren.eq(
                    Cat(
                        Replicate(self.bus.sel[2*i], 2),
                        Replicate(self.bus.sel[2*i + 1], 2),
                    )
                ),
                wren.eq(self.bus.we & self.bus.stb & self.bus.cyc)
            ]

            self.specials.spram = Instance("SB_SPRAM256KA",
                i_ADDRESS=self.bus.adr[0:14], i_DATAIN=datain,
                i_MASKWREN=maskwren,
                i_WREN=wren,
                i_CHIPSELECT=C(1,1),
                i_CLOCK=ClockSignal("sys"),
                i_STANDBY=C(0,1),
                i_SLEEP=C(0,1),
                i_POWEROFF=C(1,1),
                o_DATAOUT=dataout
            )

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.stb & self.bus.cyc & ~self.bus.ack,
                self.bus.ack.eq(1)
            )
        ]
