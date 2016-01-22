from migen import *
from migen.bank.description import *
from migen.fhdl.specials import *
from migen.genlib.cdc import MultiReg
from migen.genlib.fsm import FSM, NextState
from migen.genlib.misc import chooser


class I2CShiftReg(Module, AutoCSR):
    def __init__(self, pads):

        STATUS_FULL = 1
        STATUS_EMPTY = 2

        self.shift_reg = shift_reg = CSRStorage(8, write_from_dev=True)
        self.status = status = CSRStorage(2, reset=STATUS_EMPTY, write_from_dev=True)
        self.slave_addr = slave_addr = CSRStorage(7)
        self.pads = pads

        ###

        scl_raw = Signal()
        sda_i = Signal()
        sda_raw = Signal()
        sda_drv = Signal()
        scl_drv = Signal()
        _sda_drv_reg = Signal()
        self._sda_i_async = _sda_i_async = Signal()
        self._scl_i_async = _scl_i_async = Signal()
        _scl_drv_reg = Signal()
        self.sync += _sda_drv_reg.eq(sda_drv)
        self.sync += _scl_drv_reg.eq(scl_drv)
        self.specials += [
            Tristate(pads.sda, 0, _sda_drv_reg, _sda_i_async),
            Tristate(pads.scl, 0, _scl_drv_reg, _scl_i_async),
            MultiReg(_scl_i_async, scl_raw),
            MultiReg(_sda_i_async, sda_raw),
        ]

        # for debug
        self.scl = scl_raw
        self.sda_i = sda_i
        self.sda_o = Signal()
        self.comb += self.sda_o.eq(~_sda_drv_reg)
        self.sda_oe = _sda_drv_reg

        shift_reg_full = Signal()
        shift_reg_empty = Signal()
        scl_i = Signal()
        samp_count = Signal(3)
        samp_carry = Signal()
        self.sync += [
            Cat(samp_count, samp_carry).eq(samp_count + 1),
            If(samp_carry,
                scl_i.eq(scl_raw),
                sda_i.eq(sda_raw)
            )
        ]

        scl_r = Signal()
        sda_r = Signal()
        scl_rising = Signal()
        scl_falling = Signal()
        sda_rising = Signal()
        sda_falling = Signal()
        self.sync += [
            scl_r.eq(scl_i),
            sda_r.eq(sda_i)
        ]
        self.comb += [
            shift_reg_full.eq(status.storage[0]),
            shift_reg_empty.eq(status.storage[1]),
            scl_rising.eq(scl_i & ~scl_r),
            scl_falling.eq(~scl_i & scl_r),
            sda_rising.eq(sda_i & ~sda_r),
            sda_falling.eq(~sda_i & sda_r)
        ]

        start = Signal()
        self.comb += start.eq(scl_i & sda_falling)

        din = Signal(8)
        counter = Signal(max=9)
        counter_reset = Signal()
        self.sync += [
            If(start | counter_reset, counter.eq(0)),
            If(scl_rising,
                If(counter == 8,
                    counter.eq(0)
                ).Else(
                    counter.eq(counter + 1),
                    din.eq(Cat(sda_i, din[:7]))
                )
            )
        ]

        self.din = din
        self.counter = counter

        is_read = Signal()
        update_is_read = Signal()
        self.sync += If(update_is_read, is_read.eq(din[0]))
        data_bit = Signal()

        zero_drv = Signal()
        data_drv = Signal()
        pause_drv = Signal()
        self.comb += scl_drv.eq(pause_drv)
        self.comb += If(zero_drv, sda_drv.eq(1)).Elif(data_drv,
                                                      sda_drv.eq(~data_bit))

        data_drv_en = Signal()
        data_drv_stop = Signal()
        self.sync += If(data_drv_en, data_drv.eq(1)).Elif(data_drv_stop,
                                                          data_drv.eq(0))
        self.sync += If(data_drv_en, chooser(shift_reg.storage,
                                             counter, data_bit, 8,
                                             reverse=True))
        self.submodules.fsm = fsm = FSM()

        fsm.act("WAIT_START",
            data_drv_stop.eq(1),
	    )
        fsm.act("RCV_ADDRESS",
            data_drv_stop.eq(1),
            If(counter == 8,
                If(din[1:] == slave_addr.storage,
                    update_is_read.eq(1),
                    NextState("ACK_ADDRESS0"),
                ).Else(
                    NextState("WAIT_START"),
                )
            )
        )
        fsm.act("ACK_ADDRESS0",
            counter_reset.eq(1),
            If(~scl_i, NextState("ACK_ADDRESS1")),
        )
        fsm.act("ACK_ADDRESS1",
            counter_reset.eq(1),
            zero_drv.eq(1),
            If(scl_i, NextState("ACK_ADDRESS2")),
        )
        fsm.act("ACK_ADDRESS2",
            counter_reset.eq(1),
            zero_drv.eq(1),
            If(~scl_i,
                    NextState("PAUSE")
            )
        )
        fsm.act("PAUSE",
            counter_reset.eq(1),
            pause_drv.eq(1),
            If(~shift_reg_empty & is_read,
               counter_reset.eq(1),
               NextState("DO_READ"),
            ).Elif(~shift_reg_full & ~is_read,
               NextState("DO_WRITE"),
            )
        )
        fsm.act("DO_READ",
            If(~scl_i,
                If(counter == 8,
                   data_drv_stop.eq(1),
                   status.we.eq(1),
                   status.dat_w.eq(STATUS_EMPTY),
                   NextState("ACK_READ0"),
                ).Else(
                    data_drv_en.eq(1),
                )
            )
        )
        fsm.act("ACK_READ0",
            counter_reset.eq(1),
            If(scl_rising,
               If(sda_i,
                  NextState("WAIT_START"),
               ).Else(
                  NextState("ACK_READ1"),
               )
            )
        )
        fsm.act("ACK_READ1",
            counter_reset.eq(1),
            If(scl_falling,
               NextState("PAUSE"),
            )
        )
        fsm.act("DO_WRITE",
            If(counter == 8,
                shift_reg.dat_w.eq(din),
                shift_reg.we.eq(1),
                NextState("ACK_WRITE0"),
            )
        )
        fsm.act("ACK_WRITE0",
            counter_reset.eq(1),
            If(~scl_i, NextState("ACK_WRITE1")),
        )
        fsm.act("ACK_WRITE1",
            counter_reset.eq(1),
            zero_drv.eq(1),
            If(scl_i, NextState("ACK_WRITE2")),
        )
        fsm.act("ACK_WRITE2",
            counter_reset.eq(1),
            zero_drv.eq(1),
            If(~scl_i,
                NextState("PAUSE"),
                status.we.eq(1),
                status.dat_w.eq(STATUS_FULL),
            )
        )

        for state in fsm.actions.keys():
            fsm.act(state, If(start, NextState("RCV_ADDRESS")))

        for state in fsm.actions.keys():
            fsm.act(state, If(self.slave_addr.re, NextState("WAIT_START")))

