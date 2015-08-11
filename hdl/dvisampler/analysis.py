from migen.fhdl.std import *
from migen.genlib.cdc import MultiReg, PulseSynchronizer
from migen.genlib.fifo import AsyncFIFO
from migen.genlib.record import Record
from migen.bank.description import *
from migen.flow.actor import *

from hdl.dvisampler.common import channel_layout

from hdl.csc.rgb2ycbcr import RGB2YCbCr
from hdl.csc.ycbcr444to422 import YCbCr444to422

class SyncPolarity(Module):
    def __init__(self):
        self.valid_i = Signal()
        self.data_in0 = Record(channel_layout)
        self.data_in1 = Record(channel_layout)
        self.data_in2 = Record(channel_layout)

        self.valid_o = Signal()
        self.de = Signal()
        self.hsync = Signal()
        self.vsync = Signal()
        self.r = Signal(8)
        self.g = Signal(8)
        self.b = Signal(8)

        ###

        de = self.data_in0.de
        de_r = Signal()
        c = self.data_in0.c
        c_polarity = Signal(2)
        c_out = Signal(2)

        self.comb += [
            self.de.eq(de_r),
            self.hsync.eq(c_out[0]),
            self.vsync.eq(c_out[1])
        ]

        self.sync.pix += [
            self.valid_o.eq(self.valid_i),
            self.r.eq(self.data_in2.d),
            self.g.eq(self.data_in1.d),
            self.b.eq(self.data_in0.d),

            de_r.eq(de),
            If(de_r & ~de,
                c_polarity.eq(c),
                c_out.eq(0)
            ).Else(
                c_out.eq(c ^ c_polarity)
            )
        ]


class ResolutionDetection(Module, AutoCSR):
    def __init__(self, nbits=11):
        self.valid_i = Signal()
        self.vsync = Signal()
        self.de = Signal()

        self._hres = CSRStatus(nbits)
        self._vres = CSRStatus(nbits)

        ###

        # Detect DE transitions
        de_r = Signal()
        pn_de = Signal()
        self.sync.pix += de_r.eq(self.de)
        self.comb += pn_de.eq(~self.de & de_r)

        # HRES
        hcounter = Signal(nbits)
        self.sync.pix += If(self.valid_i & self.de,
                hcounter.eq(hcounter + 1)
            ).Else(
                hcounter.eq(0)
            )

        hcounter_st = Signal(nbits)
        self.sync.pix += If(self.valid_i,
                If(pn_de, hcounter_st.eq(hcounter))
            ).Else(
                hcounter_st.eq(0)
            )
        self.specials += MultiReg(hcounter_st, self._hres.status)

        # VRES
        vsync_r = Signal()
        p_vsync = Signal()
        self.sync.pix += vsync_r.eq(self.vsync),
        self.comb += p_vsync.eq(self.vsync & ~vsync_r)

        vcounter = Signal(nbits)
        self.sync.pix += If(self.valid_i & p_vsync,
                vcounter.eq(0)
            ).Elif(pn_de,
                vcounter.eq(vcounter + 1)
            )

        vcounter_st = Signal(nbits)
        self.sync.pix += If(self.valid_i,
                If(p_vsync, vcounter_st.eq(vcounter))
            ).Else(
                vcounter_st.eq(0)
            )
        self.specials += MultiReg(vcounter_st, self._vres.status)


class FrameExtraction(Module, AutoCSR):
    def __init__(self, word_width, fifo_depth):
        # in pix clock domain
        self.valid_i = Signal()
        self.vsync = Signal()
        self.de = Signal()
        self.r = Signal(8)
        self.g = Signal(8)
        self.b = Signal(8)

        # in sys clock domain
        word_layout = [("sof", 1), ("pixels", word_width)]
        self.frame = Source(word_layout)
        self.busy = Signal()

        self._overflow = CSR()

        ###

        de_r = Signal()
        self.sync.pix += de_r.eq(self.de)

        rgb2ycbcr = RGB2YCbCr()
        self.submodules += RenameClockDomains(rgb2ycbcr, "pix")
        chroma_downsampler = YCbCr444to422()
        self.submodules += RenameClockDomains(chroma_downsampler, "pix")
        self.comb += [
            rgb2ycbcr.sink.stb.eq(self.valid_i),
            rgb2ycbcr.sink.sop.eq(self.de & ~de_r),
            rgb2ycbcr.sink.r.eq(self.r),
            rgb2ycbcr.sink.g.eq(self.g),
            rgb2ycbcr.sink.b.eq(self.b),
            Record.connect(rgb2ycbcr.source, chroma_downsampler.sink),
            chroma_downsampler.source.ack.eq(1)
        ]
        # XXX need clean up
        de = self.de
        vsync = self.vsync
        for i in range(rgb2ycbcr.latency + chroma_downsampler.latency):
            next_de = Signal()
            next_vsync = Signal()
            self.sync.pix += [
                next_de.eq(de),
                next_vsync.eq(vsync)
            ]
            de = next_de
            vsync = next_vsync

        # start of frame detection
        vsync_r = Signal()
        new_frame = Signal()
        self.comb += new_frame.eq(vsync & ~vsync_r)
        self.sync.pix += vsync_r.eq(vsync)

        # pack pixels into words
        cur_word = Signal(word_width)
        cur_word_valid = Signal()
        encoded_pixel = Signal(16)
        self.comb += encoded_pixel.eq(Cat(chroma_downsampler.source.y, chroma_downsampler.source.cb_cr)),
        pack_factor = word_width//16
        assert(pack_factor & (pack_factor - 1) == 0)  # only support powers of 2
        pack_counter = Signal(max=pack_factor)
        self.sync.pix += [
            cur_word_valid.eq(0),
            If(new_frame,
                cur_word_valid.eq(pack_counter == (pack_factor - 1)),
                pack_counter.eq(0),
            ).Elif(chroma_downsampler.source.stb & de,
                [If(pack_counter == (pack_factor-i-1),
                    cur_word[16*i:16*(i+1)].eq(encoded_pixel)) for i in range(pack_factor)],
                cur_word_valid.eq(pack_counter == (pack_factor - 1)),
                pack_counter.eq(pack_counter + 1)
            )
        ]

        # FIFO
        fifo = RenameClockDomains(AsyncFIFO(word_layout, fifo_depth),
            {"write": "pix", "read": "sys"})
        self.submodules += fifo
        self.comb += [
            fifo.din.pixels.eq(cur_word),
            fifo.we.eq(cur_word_valid)
        ]
        self.sync.pix += \
            If(new_frame,
                fifo.din.sof.eq(1)
            ).Elif(cur_word_valid,
                fifo.din.sof.eq(0)
            )

        self.comb += [
            self.frame.stb.eq(fifo.readable),
            self.frame.payload.eq(fifo.dout),
            fifo.re.eq(self.frame.ack),
            self.busy.eq(0)
        ]

        # overflow detection
        pix_overflow = Signal()
        pix_overflow_reset = Signal()
        self.sync.pix += [
            If(fifo.we & ~fifo.writable,
                pix_overflow.eq(1)
            ).Elif(pix_overflow_reset,
                pix_overflow.eq(0)
            )
        ]

        sys_overflow = Signal()
        self.specials += MultiReg(pix_overflow, sys_overflow)
        self.submodules.overflow_reset = PulseSynchronizer("sys", "pix")
        self.submodules.overflow_reset_ack = PulseSynchronizer("pix", "sys")
        self.comb += [
            pix_overflow_reset.eq(self.overflow_reset.o),
            self.overflow_reset_ack.i.eq(pix_overflow_reset)
        ]

        overflow_mask = Signal()
        self.comb += [
            self._overflow.w.eq(sys_overflow & ~overflow_mask),
            self.overflow_reset.i.eq(self._overflow.re)
        ]
        self.sync += \
            If(self._overflow.re,
                overflow_mask.eq(1)
            ).Elif(self.overflow_reset_ack.o,
                overflow_mask.eq(0)
            )
