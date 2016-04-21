# Simple Processor Interface

from litex.gen import *
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *


# layout is a list of tuples, either:
# - (name, nbits, [reset value], [alignment bits])
# - (name, sublayout)

def _convert_layout(layout):
    r = []
    for element in layout:
        if isinstance(element[1], list):
            r.append((element[0], _convert_layout(element[1])))
        else:
            r.append((element[0], element[1]))
    return r

(MODE_EXTERNAL, MODE_SINGLE_SHOT, MODE_CONTINUOUS) = range(3)


class SingleGenerator(Module, AutoCSR):
    def __init__(self, layout, mode):
        self.source = stream.Endpoint(_convert_layout(layout))
        self.busy = Signal()

        self.comb += self.busy.eq(self.source.valid)

        if mode == MODE_EXTERNAL:
            self.trigger = Signal()
            trigger = self.trigger
        elif mode == MODE_SINGLE_SHOT:
            self._shoot = CSR()
            trigger = self._shoot.re
        elif mode == MODE_CONTINUOUS:
            self._enable = CSRStorage()
            trigger = self._enable.storage
        else:
            raise ValueError
        self.sync += If(self.source.ready | ~self.source.valid, self.source.valid.eq(trigger))

        self._create_csrs(layout, self.source.payload, mode != MODE_SINGLE_SHOT)

    def _create_csrs(self, layout, target, atomic, prefix=""):
        for element in layout:
            if isinstance(element[1], list):
                self._create_csrs(element[1], atomic,
                    getattr(target, element[0]),
                    element[0] + "_")
            else:
                name = element[0]
                nbits = element[1]
                if len(element) > 2:
                    reset = element[2]
                else:
                    reset = 0
                if len(element) > 3:
                    alignment = element[3]
                else:
                    alignment = 0
                regname = prefix + name
                reg = CSRStorage(nbits + alignment, reset=reset, atomic_write=atomic,
                    alignment_bits=alignment, name=regname)
                setattr(self, "_"+regname, reg)
                self.sync += If(self.source.ready | ~self.source.valid,
                    getattr(target, name).eq(reg.storage))


# Generates integers from start to maximum-1
class IntSequence(Module):
    def __init__(self, nbits, offsetbits=0, step=1):
        sink_layout = [("maximum", nbits)]
        if offsetbits:
            sink_layout.append(("offset", offsetbits))

        self.sink = stream.Endpoint(sink_layout)
        self.source = stream.Endpoint([("value", max(nbits, offsetbits))])

        # # #

        load = Signal()
        ce = Signal()
        last = Signal()

        maximum = Signal(nbits)
        if offsetbits:
            offset = Signal(offsetbits)
        counter = Signal(nbits)

        if step > 1:
            self.comb += last.eq(counter + step >= maximum)
        else:
            self.comb += last.eq(counter + 1 == maximum)
        self.sync += [
            If(load,
                counter.eq(0),
                maximum.eq(self.sink.maximum),
                offset.eq(self.sink.offset) if offsetbits else None
            ).Elif(ce,
                If(last,
                    counter.eq(0)
                ).Else(
                    counter.eq(counter + step)
                )
            )
        ]
        if offsetbits:
            self.comb += self.source.value.eq(counter + offset)
        else:
            self.comb += self.source.value.eq(counter)

        self.submodules.fsm = fsm = FSM()
        fsm.act("IDLE",
            load.eq(1),
            self.sink.ready.eq(1),
            If(self.sink.valid,
                NextState("ACTIVE")
            )
        )
        fsm.act("ACTIVE",
            self.source.valid.eq(1),
            If(self.source.ready,
                ce.eq(1),
                If(last,
                    NextState("IDLE")
                )
            )
        )


class _DMAController(Module):
    def __init__(self, bus_accessor, bus_aw, bus_dw, mode, base_reset=0, length_reset=0):
        self.alignment_bits = bits_for(bus_dw//8) - 1
        layout = [
            ("length", bus_aw + self.alignment_bits, length_reset, self.alignment_bits),
            ("base", bus_aw + self.alignment_bits, base_reset, self.alignment_bits)
        ]
        self.generator = SingleGenerator(layout, mode)
        self._busy = CSRStatus()

        self.length = self.generator._length.storage
        self.base = self.generator._base.storage
        if hasattr(self.generator, "trigger"):
            self.trigger = self.generator.trigger

    def get_csrs(self):
        return self.generator.get_csrs() + [self._busy]


class DMAReadController(_DMAController):
    def __init__(self, bus_accessor, *args, **kwargs):
        bus_aw = len(bus_accessor.sink.address)
        bus_dw = len(bus_accessor.source.data)
        _DMAController.__init__(self, bus_accessor, bus_aw, bus_dw, *args, **kwargs)

        self.submodules.intseq = IntSequence(bus_aw, bus_aw)

        self.comb += [
            # generator --> intseq
            self.intseq.sink.valid.eq(self.generator.source.valid),
            self.intseq.sink.maximum.eq(self.generator.source.length),
            self.intseq.sink.offset.eq(self.generator.source.base),
            self.generator.source.ready.eq(self.intseq.sink.ready),

            # intseq --> bus accessor
            bus_accessor.sink.valid.eq(self.intseq.source.valid),
            bus_accessor.sink.address.eq(self.intseq.source.value),
            self.intseq.source.ready.eq(bus_accessor.sink.ready)
        ]

        self.source = bus_accessor.source
        self.busy = 0 # XXX use last signal?
        self.comb += self._busy.status.eq(self.busy)
