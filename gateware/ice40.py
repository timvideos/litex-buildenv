from migen import *
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage


class SPRAM(Module):
    """
    ICE40 UltraPlus family-specific Wishbone interface to the Single Port RAM
    (SPRAM) primitives. Because SPRAM is much more coarse grained than Block
    RAM resources, this RAM is only minimally configurable at present (64kB or
    128kB). Because it is single port, this module is meant to be used as the
    CPU's RAM region, leaving block RAM free for other use.
    """

    def __init__(self, width=32, size=64*1024):

        # Right now, LiteX only supports 32-bit CPUs. To get a 32-bit data bus,
        # we must width-cascade 2 16-bit SPRAMs. We've already used 2 out of 4
        # SPRAMs for this, so the only other valid config is using all 4 SPRAMs
        # by depth-cascading.
        if width != 32:
            raise ValueError("Width of Up5kSPRAM must be 32 bits")
        if size != 64*1024 and size != 128*1024:
            raise ValueError("Size of Up5kSPRAM must be 64kB or 128kB.")

        self.bus = wishbone.Interface(width)

        bytesels = []
        for i in range(0, 2):
            datain = Signal(16)
            dataout = Signal(16)
            maskwren = Signal(4)
            wren = Signal(1)

            # 64k vs 128k-specific routing signals.
            datain0 = Signal(16)
            dataout0 = Signal(16)
            maskwren0 = Signal(4)

            if size == 128 * 1024:
                datain1 = Signal(16)
                dataout1 = Signal(16)
                maskwren1 = Signal(4)

            # Generic routing common to all depths.
            for j in range(16):
                self.comb += [self.bus.dat_r[16*i + j].eq(dataout[j])]

            self.comb += [
                datain.eq(self.bus.dat_w[16*i:16*i+16]),
                # MASKWREN is nibble-based, interestingly enough.
                maskwren.eq(
                    Cat(
                        Replicate(self.bus.sel[2*i], 2),
                        Replicate(self.bus.sel[2*i + 1], 2),
                    )
                ),
                wren.eq(self.bus.we & self.bus.stb & self.bus.cyc)
            ]

            # Signals which must be routed differently based on depth.
            # 64kB
            if size == 64*1024:
                self.comb += [
                    datain0.eq(datain),
                    dataout.eq(dataout0),
                    maskwren0.eq(maskwren)
                ]
            # 128kB
            else:
                self.comb += [
                    If(self.bus.adr[14],
                        datain1.eq(datain),
                        dataout.eq(dataout1),
                        maskwren1.eq(maskwren)
                    ).Else(
                        datain0.eq(datain),
                        dataout.eq(dataout0),
                        maskwren0.eq(maskwren)
                    )
                ]

            self.specials.spram = Instance("SB_SPRAM256KA",
                i_ADDRESS=self.bus.adr[0:14], i_DATAIN=datain0,
                i_MASKWREN=maskwren0,
                i_WREN=wren,
                i_CHIPSELECT=C(1,1),
                i_CLOCK=ClockSignal("sys"),
                i_STANDBY=C(0,1),
                i_SLEEP=C(0,1),
                i_POWEROFF=C(1,1),
                o_DATAOUT=dataout0
            )

            # We need to depth cascade if using 128kB.
            if size == 128*1024:
                self.specials.spram = Instance("SB_SPRAM256KA",
                    i_ADDRESS=self.bus.adr[0:14], i_DATAIN=datain1,
                    i_MASKWREN=maskwren1,
                    i_WREN=wren,
                    i_CHIPSELECT=C(1,1),
                    i_CLOCK=ClockSignal("sys"),
                    i_STANDBY=C(0,1),
                    i_SLEEP=C(0,1),
                    i_POWEROFF=C(1,1),
                    o_DATAOUT=dataout1
                )

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.stb & self.bus.cyc & ~self.bus.ack,
                self.bus.ack.eq(1)
            )
        ]


class LED(Module, AutoCSR):
    def __init__(self, pads):

        rgba_pwm = Signal(3)

        self.dat = CSRStorage(8)
        self.addr = CSRStorage(4)
        self.ctrl = CSRStorage(4)

        self.specials += Instance("SB_RGBA_DRV",
            i_CURREN = self.ctrl.storage[1],
            i_RGBLEDEN = self.ctrl.storage[2],
            i_RGB0PWM = rgba_pwm[0],
            i_RGB1PWM = rgba_pwm[1],
            i_RGB2PWM = rgba_pwm[2],
            o_RGB0 = pads.rgb0,
            o_RGB1 = pads.rgb1,
            o_RGB2 = pads.rgb2,
            p_CURRENT_MODE = "0b1",
            p_RGB0_CURRENT = "0b000011",
            p_RGB1_CURRENT = "0b000001",
            p_RGB2_CURRENT = "0b000011",
        )

        self.specials += Instance("SB_LEDDA_IP",
            i_LEDDCS = self.dat.re,
            i_LEDDCLK = ClockSignal(),
            i_LEDDDAT7 = self.dat.storage[7],
            i_LEDDDAT6 = self.dat.storage[6],
            i_LEDDDAT5 = self.dat.storage[5],
            i_LEDDDAT4 = self.dat.storage[4],
            i_LEDDDAT3 = self.dat.storage[3],
            i_LEDDDAT2 = self.dat.storage[2],
            i_LEDDDAT1 = self.dat.storage[1],
            i_LEDDDAT0 = self.dat.storage[0],
            i_LEDDADDR3 = self.addr.storage[3],
            i_LEDDADDR2 = self.addr.storage[2],
            i_LEDDADDR1 = self.addr.storage[1],
            i_LEDDADDR0 = self.addr.storage[0],
            i_LEDDDEN = self.dat.re,
            i_LEDDEXE = self.ctrl.storage[0],
            # o_LEDDON = led_is_on, # Indicates whether LED is on or not
            # i_LEDDRST = ResetSignal(), # This port doesn't actually exist
            o_PWMOUT0 = rgba_pwm[0],
            o_PWMOUT1 = rgba_pwm[1],
            o_PWMOUT2 = rgba_pwm[2],
            o_LEDDON = Signal(),
        )

class SBWarmBoot(Module, AutoCSR):
    def __init__(self, parent):
        self.ctrl = CSRStorage(size=8)
        self.addr = CSRStorage(size=32)
        do_reset = Signal()
        self.comb += [
            # "Reset Key" is 0xac (0b101011xx)
            do_reset.eq(self.ctrl.storage[2] & self.ctrl.storage[3] & ~self.ctrl.storage[4]
                      & self.ctrl.storage[5] & ~self.ctrl.storage[6] & self.ctrl.storage[7])
        ]
        self.specials += Instance("SB_WARMBOOT",
            i_S0   = self.ctrl.storage[0],
            i_S1   = self.ctrl.storage[1],
            i_BOOT = do_reset,
        )
        parent.config["BITSTREAM_SYNC_HEADER1"] = 0x7e99aa7e
        parent.config["BITSTREAM_SYNC_HEADER2"] = 0x7eaa997e


