import os

from migen.fhdl.std import *
from migen.genlib.record import *
from migen.flow.actor import *
from migen.actorlib.fifo import SyncFIFO
from migen.genlib.misc import WaitTimer


class UDPStreamer(Module):
    def __init__(self, ip_address, udp_port, fifo_depth=1024):
        self.sink = sink = Sink([("data", 8)])
        self.source = source = Source(eth_udp_user_description(8))

        # # #

        self.submodules.fifo = fifo = SyncFIFO([("data", 8)], fifo_depth)
        self.comb += Record.connect(sink, fifo.sink)

        self.submodules.level = level = FlipFlop(max=fifo_depth+1)
        self.comb += level.d.eq(fifo.fifo.level)

        self.submodules.counter = counter = Counter(max=fifo_depth)

        self.submodules.flush_timer = WaitTimer(10000)
        flush = Signal()
        self.comb += [
            flush.eq((fifo.fifo.level > 0) & self.flush_timer.done)
        ]

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
          self.flush_timer.wait.eq(1),
            If((fifo.fifo.level >= 256) | flush,
                level.ce.eq(1),
                counter.reset.eq(1),
                NextState("SEND")
            )
        )
        fsm.act("SEND",
            source.stb.eq(fifo.source.stb),
            source.sop.eq(counter.value == 0),
            If(level.q == 0,
                source.eop.eq(1),
            ).Else(
                source.eop.eq(counter.value == (level.q-1)),
            ),
            source.src_port.eq(udp_port),
            source.dst_port.eq(udp_port),
            source.ip_address.eq(ip_address),
            If(level.q == 0,
                source.length.eq(1),
            ).Else(
                source.length.eq(level.q),
            ),
            source.data.eq(fifo.source.data),
            fifo.source.ack.eq(source.ack),
            If(source.stb & source.ack,
                counter.ce.eq(1),
                If(source.eop,
                    NextState("IDLE")
                )
            )
        )


class USBStreamer(Module):
    def __init__(self, platform, pads):
        self.sink = sink = Sink([("data", 8)])

        # # #

        self.comb += pads.slcs.eq(0)

        jpeg_fifo_full = Signal()
        self.comb += self.sink.ack.eq(~jpeg_fifo_full)

        # XXX for now use simplified usb_top from HDMI2USB
        self.specials += Instance("usb_streamer",
                                  # clk, rst
                                  i_rst=ResetSignal(),
                                  i_clk=ClockSignal(),

                                  # jpeg encoder interface
                                  i_jpeg_byte=self.sink.data,
                                  i_jpeg_clk=ClockSignal(),
                                  i_jpeg_en=self.sink.stb & self.sink.ack,
                                  o_jpeg_fifo_full=jpeg_fifo_full,

                                  # cypress fx2 slave fifo interface
                                  i_ifclk=pads.ifclk,
                                  io_fdata=pads.data,
                                  i_flag_full=pads.flagb,
                                  i_flag_empty=pads.flagc,
                                  o_faddr=pads.addr,
                                  o_slwr=pads.slwr,
                                  o_slrd=pads.slrd,
                                  o_sloe=pads.sloe,
                                  o_pktend=pads.pktend
        )

        # add VHDL sources
        platform.add_source_dir(os.path.join(platform.soc_ext_path, "hdl", "stream", "vhdl"))
