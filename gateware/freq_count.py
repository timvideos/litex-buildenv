from litex.gen import *
from litex.gen.genlib.cdc import GrayCounter
from litex.soc.interconnect.csr import *


# Essentially an "Always-enabled GrayCounter with a separate clock domain."
@ClockDomainsRenamer("src")
class EventGrayCounter(GrayCounter):
    """Gray counter with reset.

    This module subclasses GrayCounter, making it always enabled and
    usable in a separate clock domain from cd_sys. Each positive edge
    of the src clock domain will increment the counter.

    Parameters
    ----------
    width: int
        Width of the counter

    Attributes
    ----------
    ce: Signal, in
        Chip-enable.
    q: list of Signals, out
        Current gray-encoded counter output, incremented each clock.
    """
    def __init__(self, width):
        GrayCounter.__init__(self, width)

        ###
        self.comb += [self.ce.eq(1)]


class Synchronizer(Module):
    """A register suitable for clock-domain crossings.

    Synchronizer takes an gray-encoded input signal from one clock
    domain and safely transfers the signal to another clock domain.

    Parameters
    ----------
    width : int
        Width of the register

    Attributes
    ----------
    inp : list of Signals, in
        Source clock domain input.

    out : list of Signals, out
        Destination clock domain output.

    Notes
    -----
    By default, the source clock domain is sys, and the source clock
    domain is dest. Make sure to instantiate these clock domains, or
    use the ClockDomainsRenamer decorator.
    """
    def __init__(self, width):
        self.inp = Signal(width)
        stage1 = Signal(width)
        self.out = Signal(width)

        ###
        self.sync.dest += [stage1.eq(self.inp),
                           self.out.eq(stage1)]


class GrayToBinary(Module):
    """Convert a Gray code value to standard binary representation.

    Parameters
    ----------
    width : int
        Width of the conversion.

    Attributes
    ----------
    gray_in : list of Signals, in
        Gray-encoded input.
    binary_out : list of Signals, out
        Binary-encoded output.
    """
    def __init__(self, width):
        self.gray_in = Signal(width)
        self.binary_out = Signal(width)

        ###
        self.comb += [self.binary_out[-1].eq(self.gray_in[-1])]

        for n in range(width - 2, -1, -1):
            self.comb += [self.binary_out[n].eq(self.binary_out[n + 1]
                          ^ self.gray_in[n])]


@ResetInserter
class Counter(Module):
    """Counter with reset.

    Parameters
    ----------
    width : int
        Width of the counter

    Attributes
    ----------
    reset : Signal, in
        Reset the counter to 0 when asserted.
    count : list of Signals, out
        Counter output.
    """
    def __init__(self, width):
        self.count = Signal(width)

        ###
        self.sync.dest += [self.count.eq(self.count + 1)]


@ResetInserter()
class FlipFlop(Module):
    """Flip-flop with reset.

    Parameters
    ----------
    width : int
        Width of the flip-flop

    Attributes
    ----------
    reset : Signal, in
        Reset flip-flop to 0 when asserted.
    inp : list of Signals, in
        Flip-flop input to be latched to output, next clock cycle.
    out : list of Signals, out
        Current flip-flop latched value.
    """
    def __init__(self, width):
        self.inp = Signal(width)
        self.out = Signal(width)

        ###
        self.sync.dest += [self.out.eq(self.inp)]


class Sampler(Module):
    """Increment an internal accumulator each destination clock tick.

    Every clock tick in the destination clock domain, Sampler will
    latch the number of ticks counted from the source clock domain,
    and add them to an internal accumulator. The source clock tick
    counter should then be reset be external means, and counting will
    repeat until the next tick in the destination clock domain.

    Parameters
    ----------
    sample_width : int
        Width of the source clock domain counter. In theory, this
        limits the maximum number of events which can be counted
        in a single destination clock tick to 2**width - 1 source
        ticks.
    full_width: int
        Width of the internal accumulator.

    Attributes
    ----------
    sample_in : list of Signals, in
        Number of events counted in the source clock domain, generated
        externally.
    end_period : Signal, in
        Reset the internal accumulator to 0.
    last_total : list of Signals, out
        Register holding the total number of source events counted
        since the previous end_period (or system reset).
    inc : list of Signals, out

    curr_total.out : list of Signals, out
        Internal signal holding the current number of source events
        counted since the previous end_period (or system reset).
    """
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
    """Frequency counter.

    FreqCountCore provides an interface to a full-fledged frequency
    counter, which can be wrapped in a higher-level class to add
    as an I/O peripheral on a CPU bus.

    Parameters
    ----------
    sample_width : int
        Width of the source clock domain counter. In theory, this
        limits the maximum number of events which can be counted
        in a single destination clock tick to 2**width - 1 source
        ticks.
    full_width : int
        Width of the internal accumulator.

    Attributes
    ----------
    count_curr : list of Signals, out
        Number of source ticks currently elapsed in the
        current sampling period.
    count_latched : list of Signals, out
        Number of source ticks total in last sampling period.
    latch : Signal, in
        Latch and reset the internal accumulator.
    cd_src : ClockDomain, in
        Source clock domain object. The clk attribute is the signal
        of interest to count.
    cd_dest : ClockDomain, in
        Destination clock domain object. The clk and rst attribute
        drive the rest of the design.

    Notes
    -----
    The frequency counter's design was inspired by ideas discussed on
    this page:
    http://hamsterworks.co.nz/mediawiki/index.php/High_Speed_Frequency_Counter

    The default clock domains are named src and dest respectively.
    These can be overidden using ClockDomainsRenamer, or accessing
    the clock domains directly.
    """
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
                      self.gray2bin.gray_in.eq(
                          self.clk_sync.out),
                      self.sampler.sample_in.eq(
                          self.gray2bin.binary_out),
                      self.count_latched.eq(
                          self.sampler.last_total),
                      self.count_curr.eq(
                          self.sampler.curr_total.out),
                      self.sampler.end_period.eq(
                          self.latch)]


class FrequencyCounter(Module, AutoCSR):
    """Frequency counter using the CSR bus.

    FrequencyCounter wraps around FreqCountCore and offers a CSR-bus
    interface to a frequency counter. Attaching this as a submodule
    in a MiSoC design, and assigning an address to csr_peripherals
    should be sufficient to generate proper API access functions and
    add as an I/O peripheral on a SoC.

    Parameters
    ----------
    sample_clk_ticks : int
        Number of clock ticks in the destination clock domain that
        should elapsed before FreqCountCore latches/resets the
        Sampler's internal accumulator.
    sample_width : int
        Width of the source clock domain counter. In theory, this
        limits the maximum number of events which can be counted
        in a single destination clock tick to 2**width - 1 source
        ticks.
    full_width : int
        Width of the internal accumulator.

    Attributes
    ----------
    core : FreqCountCore
        Access to all of FreqCountCore's signals is provided through
        this attribute.

    Registers
    ---------
    value : Number of source ticks total in last sampling period.
    num_events : Number of source ticks currently elapsed in the
        current sampling period.
    num_samples: Number of elapsed dest clock ticks in current period.
    last_inc: Number of elapsed source ticks in last sample. This
        value was routed up from a signal used internally by Sampler
        and should not otherwise be used.

    Notes
    -----
    If the sample_clk_ticks value does not coincide with the dest
    clock frequency, it is the user's responsibility to calculate
    the frequency by converting the unit of time measured to 1 second.
    """
    def __init__(self, sample_clk_ticks, sample_width, full_width):
        self.value = CSRStatus(full_width)
        self.num_events = CSRStatus(full_width)
        self.num_samples = CSRStatus(full_width)
        self.last_inc = CSRStatus(sample_width)

        # TODO: Perhaps configure the number of dest clk ticks before
        # number of events is latched?

        self.submodules.core = FreqCountCore(sample_width, full_width)

        ###
        self.comb += [self.value.status.eq(self.core.count_latched),
                      self.num_events.status.eq(self.core.count_curr),
                      self.last_inc.status.eq(self.core.sampler.inc)]

        # sample_clk_ticks = 0 is a legal sample period.
        # It means sample each cycle.
        self.sync.dest += [self.core.latch.eq(0),
                           If(self.num_samples.status ==
                              sample_clk_ticks,
                              self.num_samples.status.eq(0),
                              self.core.latch.eq(1)).
                           Else(self.num_samples.status.eq(
                                    self.num_samples.status + 1))]