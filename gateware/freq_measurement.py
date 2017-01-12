from litex.gen import *
from litex.gen.genlib.cdc import MultiReg, GrayCounter
from litex.gen.genlib.cdc import GrayDecoder
from litex.soc.interconnect.csr import *


class Sampler(Module):
    def __init__(self, measure_width, counter_width):
        self.sample_in = Signal(measure_width)
        self.inc = Signal(measure_width)
        self.last_total = Signal(counter_width)
        self.end_period = Signal()

        last_sample = Signal(measure_width)
        curr_total = Signal(counter_width)

        # # #

        self.sync += last_sample.eq(self.sample_in)
        # Resetting souce clock domain is unreliable, so just use wrapping
        # property of unsigned arithmetic to reset the count each sample.
        self.comb += self.inc.eq(self.sample_in - last_sample)
        self.sync += \
            If(self.end_period,
                curr_total.eq(0)
            ).Else(
                curr_total.eq(curr_total + self.inc)
            )

        # During period reset, curr_total won't latch the final value, so
        # store it in separate location.
        self.sync += \
            If(self.end_period,
                self.last_total.eq(curr_total)
            )


class Measurement(Module):
    def __init__(self, measure_clock, measure_width, counter_width):
        self.value = Signal(counter_width)
        self.latch = Signal()

        ev_count = ClockDomainsRenamer("measure")(GrayCounter(measure_width))
        gray_decoder = GrayDecoder(measure_width)
        sampler = Sampler(measure_width, counter_width)
        self.submodules += ev_count, gray_decoder, sampler

        self.clock_domains.cd_measure = ClockDomain(reset_less=True)
        if isinstance(measure_clock, str):
            self.comb += self.cd_measure.clk.eq(ClockSignal(measure_clock))
        else:
            self.comb += self.cd_measure.clk.eq(measure_clock)

        self.comb += ev_count.ce.eq(1)
        self.specials += MultiReg(ev_count.q, gray_decoder.i)

        # # #

        self.comb += [
            sampler.end_period.eq(self.latch),
            sampler.sample_in.eq(gray_decoder.o),
            self.value.eq(sampler.last_total)
        ]


class FrequencyMeasurement(Module, AutoCSR):
    def __init__(self, measure_clock, measure_period, 
            measure_width=6, counter_width=32):
        self.value = CSRStatus(counter_width)

        # # #

        core = Measurement(measure_clock, measure_width, counter_width)
        self.submodules += core

        self.comb += self.value.status.eq(core.value)

        period_done = Signal()
        period_counter = Signal(counter_width)
        self.comb += [
            period_done.eq(period_counter == measure_period),
            core.latch.eq(period_done)
        ]
        self.sync += \
            If(period_done,
                period_counter.eq(0),
            ).Else(
                period_counter.eq(period_counter + 1)
            )
