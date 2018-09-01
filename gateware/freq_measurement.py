from migen import *
from migen.genlib.cdc import MultiReg, GrayCounter
from migen.genlib.cdc import GrayDecoder
from litex.soc.interconnect.csr import *


class Sampler(Module):
    def __init__(self, measure_width, counter_width):
        self.i = Signal(measure_width)
        self.latch = Signal()
        self.value = Signal(counter_width)


        # # #

        counter = Signal(counter_width)
        counter_inc = Signal(measure_width)

        # use wrapping property of unsigned arithmeric to reset the counter
        # each cycle (reseting measure clock domain is unreliable)
        i_d = Signal(measure_width)
        self.sync += i_d.eq(self.i)
        self.comb += counter_inc.eq(self.i - i_d)

        self.sync += \
            If(self.latch,
                counter.eq(0),
                self.value.eq(counter),
            ).Else(
                counter.eq(counter + counter_inc)
            )


class FrequencyMeasurement(Module, AutoCSR):
    def __init__(self, measure_clock, measure_period,
            measure_width=6, counter_width=32):
        self.value = CSRStatus(counter_width)

        # # #

        # create measure clock domain
        self.clock_domains.cd_measure = ClockDomain(reset_less=True)
        self.comb += self.cd_measure.clk.eq(measure_clock)

        # mesure period
        period_done = Signal()
        period_counter = Signal(counter_width)
        self.comb += period_done.eq(period_counter == measure_period)
        self.sync += \
            If(period_done,
                period_counter.eq(0),
            ).Else(
                period_counter.eq(period_counter + 1)
            )

        # measurement
        event_counter = ClockDomainsRenamer("measure")(GrayCounter(measure_width))
        gray_decoder = GrayDecoder(measure_width)
        sampler = Sampler(measure_width, counter_width)
        self.submodules += event_counter, gray_decoder, sampler

        self.specials += MultiReg(event_counter.q, gray_decoder.i)
        self.comb += [
            event_counter.ce.eq(1),
            sampler.latch.eq(period_done),
            sampler.i.eq(gray_decoder.o),
            self.value.status.eq(sampler.value)
        ]
