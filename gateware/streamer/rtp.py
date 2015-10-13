# RTP Proof of concept, metadata informations are missing (Sync, ...)
# but this can be used as a basis to implement real RTP

rtp_header_length = 12
rtp_header_fields = {
    "ver":              HeaderField(0,  6,  2),
    "p":                HeaderField(0,  5,  1),
    "x":                HeaderField(0,  4,  1),
    "cc":               HeaderField(0,  0,  4),
    "m":                HeaderField(1,  7,  1),
    "pt":               HeaderField(1,  0,  7),
    "sequence_number":  HeaderField(2,  0,  16),
    "timestamp":        HeaderField(4,  0,  32),
    "ssrc":             HeaderField(8,  0,  32)
}
rtp_header = Header(rtp_header_fields,
                    rtp_header_length,
                    swap_field_bytes=True)


def eth_rtp_description(dw):
    param_layout = rtp_header.get_layout()
    payload_layout = [
        ("data", dw),
        ("error", dw//8)
    ]
    return EndpointDescription(payload_layout, param_layout, packetized=True)


def eth_rtp_user_description(dw):
    param_layout = [
        ("src_port", 16),
        ("dst_port", 16),
        ("ip_address", 32),
        ("length", 16)
    ]
    payload_layout = [
        ("data", dw),
        ("error", dw//8)
    ]
    return EndpointDescription(payload_layout, param_layout, packetized=True)


class EncoderRTPGenerator(Module):
    def __init__(self, ip_address, udp_port, fifo_depth=1024):
        self.sink = sink = Sink([("data", 8)])
        self.source = source = Source(eth_rtp_user_description(8))

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
          self.flush_timer.wait.eq(fifo.fifo.level > 0),
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


class EncoderRTPPacketizer(Packetizer):
    def __init__(self):
        Packetizer.__init__(self,
            eth_rtp_description(8),
            eth_udp_user_description(8),
            rtp_header)


class EncoderRTPSender(Module):
    def __init__(self):
        self.sink = sink = Sink(eth_rtp_user_description(8))
        self.source = source = Source(eth_udp_user_description(8))

        # # #

        timestamp = Signal(32)
        self.sync += timestamp.eq(timestamp+1)

        sequence_number = Counter(16)
        self.submodules += sequence_number

        self.submodules.packetizer = packetizer = EncoderRTPPacketizer()
        self.comb += [
            packetizer.sink.stb.eq(sink.stb),
            packetizer.sink.sop.eq(sink.sop),
            packetizer.sink.eop.eq(sink.eop),
            sink.ack.eq(packetizer.sink.ack),
            packetizer.sink.ver.eq(0x2),
            packetizer.sink.p.eq(0),
            packetizer.sink.x.eq(0),
            packetizer.sink.cc.eq(0),
            packetizer.sink.m.eq(0),
            packetizer.sink.pt.eq(26), #JPEG
            packetizer.sink.sequence_number.eq(sequence_number.value),
            packetizer.sink.timestamp.eq(timestamp),
            packetizer.sink.ssrc.eq(1),
            packetizer.sink.data.eq(sink.data)
        ]

        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            packetizer.source.ack.eq(1),
            If(packetizer.source.stb & packetizer.source.sop,
                packetizer.source.ack.eq(0),
                NextState("SEND")
            )
        )
        fsm.act("SEND",
            Record.connect(packetizer.source, source),
            source.src_port.eq(sink.src_port),
            source.dst_port.eq(sink.dst_port),
            source.ip_address.eq(sink.ip_address),
            source.length.eq(sink.length + rtp_header.length),
            If(source.stb & source.eop & source.ack,
                sequence_number.ce.eq(1),
                NextState("IDLE"),
            )
        )