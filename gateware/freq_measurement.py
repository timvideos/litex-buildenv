from litex.gen import *
from litex.gen.genlib.cdc import MultiReg, GrayCounter
from litex.soc.interconnect.csr import *


class GrayToBinary(Module):
    def __init__(self, width):
        self.gray_in = Signal(width)
        self.binary_out = Signal(width)

        # # #

        self.comb += self.binary_out[-1].eq(self.gray_in[-1])

        for n in range(width - 2, -1, -1):
            self.comb += [self.binary_out[n].eq(self.binary_out[n + 1]
                          ^ self.gray_in[n])]


@ResetInserter()
class FlipFlop(Module):
    def __init__(self, width):
        self.inp = Signal(width)
        self.out = Signal(width)

        # # #

        self.sync += self.out.eq(self.inp)


class Sampler(Module):
    def __init__(self, measure_width, counter_width):
        self.sample_in = Signal(measure_width)
        self.inc = Signal(measure_width)
        self.last_total = Signal(counter_width)
        self.end_period = Signal(1)

        self.submodules.last_sample = FlipFlop(measure_width)
        self.submodules.curr_total = FlipFlop(counter_width)

        # # #

        self.comb += self.last_sample.inp.eq(self.sample_in)
        # Resetting souce clock domain is unreliable, so just use wrapping
        # property of unsigned arithmetic to reset the count each sample.
        self.comb += self.inc.eq(self.sample_in - self.last_sample.out)
        self.comb += self.curr_total.inp.eq(self.curr_total.out + self.inc)
        self.comb += self.curr_total.reset.eq(self.end_period)

        # During period reset, curr_total won't latch the final value, so
        # store it in separate location.
        self.sync += \
            If(self.end_period,
                self.last_total.eq(self.curr_total.inp)
            )


class FrequencyMeasurementCore(Module):
    def __init__(self, measure_clock, measure_width, counter_width):
        self.value = Signal(counter_width)
        self.latch = Signal()

        ev_count = ClockDomainsRenamer("measure")(GrayCounter(measure_width))
        gray2bin = GrayToBinary(measure_width)
        sampler = Sampler(measure_width, counter_width)
        self.submodules += ev_count, gray2bin, sampler

        self.clock_domains.cd_measure = ClockDomain(reset_less=True)
        if isinstance(measure_clock, str):
            self.comb += self.cd_measure.clk.eq(ClockSignal(measure_clock))
        else:
            self.comb += self.cd_measure.clk.eq(measure_clock)

        self.comb += ev_count.ce.eq(1)
        self.specials += MultiReg(ev_count.q, gray2bin.gray_in)

        # # #

        self.comb += [
            sampler.end_period.eq(self.latch),
            sampler.sample_in.eq(gray2bin.binary_out),
            self.value.eq(sampler.last_total),
        ]


class FrequencyMeasurement(Module, AutoCSR):
    def __init__(self, measure_clock, measure_period, 
            measure_width=6, counter_width=32):
        self.value = CSRStatus(counter_width)

        # # #

        core = FrequencyMeasurementCore(measure_clock, 
                                        measure_width,
                                        counter_width)
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
