from migen.fhdl.std import *
from migen.genlib.fifo import AsyncFIFO
from migen.genlib.misc import ClockDomainsRenamer
from migen.fhdl.bitcontainer import flen
from migen.genlib.cdc import GrayCounter
from migen.bank.description import *
from migen.fhdl import verilog


# Essentially an "Always-enabled GrayCounter with a separate clock domain."
@ClockDomainsRenamer("src")
class EventGrayCounter(GrayCounter):
    def __init__(self, width):
        GrayCounter.__init__(self, width)
        self.input_sig = Signal()

        ###
        self.comb += [self.ce.eq(1)]


class Synchronizer(Module):
    def __init__(self, width):
        self.inp = Signal(width)
        stage1 = Signal(width)
        self.out = Signal(width)

        ###
        self.sync.dest += [stage1.eq(self.inp),
            self.out.eq(stage1)]


class GrayToBinary(Module):
    def __init__(self, width):
        self.gray_in = Signal(width)
        self.binary_out = Signal(width)

        ###
        self.comb += [self.binary_out[-1].eq(self.gray_in[-1])]

        for n in range(width - 2, -1, -1):
            self.comb += [self.binary_out[n].eq(self.binary_out[n + 1] ^ self.gray_in[n])]


@ResetInserter
class Counter(Module):
    def __init__(self, width):
        self.count = Signal(width)

        ###
        self.sync.dest += [self.count.eq(self.count + 1)]


@ResetInserter()
class FlipFlop(Module):
    def __init__(self, width):
        self.inp = Signal(width)
        self.out = Signal(width)

        ###
        self.sync.dest += [self.out.eq(self.inp)]


class Sampler(Module):
    def __init__(self, sample_width, full_width):
        self.sample_in = Signal(sample_width)
        self.inc = Signal(sample_width)
        self.last_total = Signal(full_width)
        self.end_period = Signal(1)

        self.submodules.last_sample = FlipFlop(sample_width)
        self.submodules.curr_total = FlipFlop(full_width)

        ###
        self.comb += [self.last_sample.inp.eq(self.sample_in)]
        # Resetting souce clock domain is unreliable, so just use wrapping
        # property of unsigned arithmetic to reset the count each sample.
        self.comb += [self.inc.eq(self.sample_in - self.last_sample.out)]
        self.comb += [self.curr_total.inp.eq(self.curr_total.out + self.inc)]
        self.comb += [self.curr_total.reset.eq(self.end_period)]

        # During period reset, curr_total won't latch the final value, so
        # store it in separate location.
        self.sync.dest += [If(self.end_period,
            self.last_total.eq(self.curr_total.inp))]


class FreqCountCore(Module):
    def __init__(self, sample_width, full_width):
        self.count_curr = Signal(full_width)
        self.count_latched = Signal(full_width)
        self.latch = Signal(1)

        self.submodules.ev_count = EventGrayCounter(sample_width)
        self.submodules.clk_sync = Synchronizer(sample_width)
        self.submodules.gray2bin = GrayToBinary(sample_width)
        self.submodules.sampler = Sampler(sample_width, full_width)

        self.clock_domains.cd_dest = ClockDomain()
        self.clock_domains.cd_src = ClockDomain(reset_less=True)

        ###
        self.comb += [self.clk_sync.inp.eq(self.ev_count.q),
            self.gray2bin.gray_in.eq(self.clk_sync.out),
            self.sampler.sample_in.eq(self.gray2bin.binary_out),
            self.count_latched.eq(self.sampler.last_total),
            self.count_curr.eq(self.sampler.curr_total.out),
            self.sampler.end_period.eq(self.latch)]


class FrequencyCounter(Module, AutoCSR):
    # sample_clk_ticks: How many clocks of the dest domain should elapsed
    # to be considered a full period.
    # sample_width: Bit width of the src domain sampling counter.
    # full_width: Bit width of the dest domain sampling counter, output being
    # the sum of all samples in the current period.

    # freq_out: Number of src eventstotal in last sampling period.
    # num_events: Number of src events in current elapsed sampling period.
    # num_samples: Number of elapsed dest clks in current period.
    # last_inc: Number of elapsed src clks in last sample.
    def __init__(self, sample_clk_ticks, sample_width, full_width):
        self.freq_out = CSRStatus(full_width)
        self.num_events = CSRStatus(full_width)
        self.num_samples = CSRStatus(full_width)
        self.last_inc = CSRStatus(sample_width)

        # TODO: Perhaps configure the number of dest clk ticks before
        # number of events is latched?

        self.submodules.core = FreqCountCore(sample_width, full_width)

        ###
        self.comb += [self.freq_out.status.eq(self.core.count_latched),
            self.num_events.status.eq(self.core.count_curr),
            self.last_inc.status.eq(self.core.sampler.inc)]

        # sample_clk_ticks = 0 is a legal sample period. It means sample each cycle.
        self.sync.dest += [self.core.latch.eq(0),
            If(self.num_samples.status == sample_clk_ticks,
                self.num_samples.status.eq(0),
                self.core.latch.eq(1)).
            Else(self.num_samples.status.eq(self.num_samples.status + 1))]
