from migen.fhdl.std import *
from migen.bank.description import AutoCSR

from gateware import freq_count
from gateware.hdmi_in.edid import EDID
from gateware.hdmi_in.clocking import Clocking
from gateware.hdmi_in.datacapture import DataCapture
from gateware.hdmi_in.charsync import CharSync
from gateware.hdmi_in.wer import WER
from gateware.hdmi_in.decoding import Decoding
from gateware.hdmi_in.chansync import ChanSync
from gateware.hdmi_in.analysis import SyncPolarity, ResolutionDetection, FrameExtraction
from gateware.hdmi_in.dma import DMA


class HDMIIn(Module, AutoCSR):
    def __init__(self, pads, lasmim, n_dma_slots=2, fifo_depth=512, soc=None):
        self.submodules.edid = EDID(pads)
        self.submodules.clocking = Clocking(pads)

        if soc:
            self.submodules.frequency = freq_count.FrequencyCounter(soc.clk_freq, 6, 32)
            # Only rename source, manually connect dest b/c of Migen decoration rules.
            # self.submodules.freq_count = ClockDomainsRenamer({"src" : "pix"})(freq_count.FrequencyCounter(80*1000000, 6, 32))
            self.comb += [
                self.frequency.core.cd_src.clk.eq(self.clocking._cd_pix.clk),
                self.frequency.core.cd_dest.clk.eq(soc.crg.cd_sys.clk),
                self.frequency.core.cd_dest.rst.eq(soc.crg.cd_sys.rst),
            ]

        for datan in range(3):
            name = "data" + str(datan)

            cap = DataCapture(getattr(pads, name + "_p"), getattr(pads, name + "_n"), 8)
            setattr(self.submodules, name + "_cap", cap)
            self.comb += cap.serdesstrobe.eq(self.clocking.serdesstrobe)

            charsync = CharSync()
            setattr(self.submodules, name + "_charsync", charsync)
            self.comb += charsync.raw_data.eq(cap.d)

            wer = WER()
            setattr(self.submodules, name + "_wer", wer)
            self.comb += wer.data.eq(charsync.data)

            decoding = Decoding()
            setattr(self.submodules, name + "_decod", decoding)
            self.comb += [
                decoding.valid_i.eq(charsync.synced),
                decoding.input.eq(charsync.data)
            ]

        self.submodules.chansync = ChanSync()
        self.comb += [
            self.chansync.valid_i.eq(self.data0_decod.valid_o & \
              self.data1_decod.valid_o & self.data2_decod.valid_o),
            self.chansync.data_in0.eq(self.data0_decod.output),
            self.chansync.data_in1.eq(self.data1_decod.output),
            self.chansync.data_in2.eq(self.data2_decod.output),
        ]

        self.submodules.syncpol = SyncPolarity()
        self.comb += [
            self.syncpol.valid_i.eq(self.chansync.chan_synced),
            self.syncpol.data_in0.eq(self.chansync.data_out0),
            self.syncpol.data_in1.eq(self.chansync.data_out1),
            self.syncpol.data_in2.eq(self.chansync.data_out2)
        ]

        self.submodules.resdetection = ResolutionDetection()
        self.comb += [
            self.resdetection.valid_i.eq(self.syncpol.valid_o),
            self.resdetection.de.eq(self.syncpol.de),
            self.resdetection.vsync.eq(self.syncpol.vsync)
        ]

        self.submodules.frame = FrameExtraction(lasmim.dw, fifo_depth)
        self.comb += [
            self.frame.valid_i.eq(self.syncpol.valid_o),
            self.frame.de.eq(self.syncpol.de),
            self.frame.vsync.eq(self.syncpol.vsync),
            self.frame.r.eq(self.syncpol.r),
            self.frame.g.eq(self.syncpol.g),
            self.frame.b.eq(self.syncpol.b)
        ]

        self.submodules.dma = DMA(lasmim, n_dma_slots)
        self.comb += self.frame.frame.connect(self.dma.frame)
        self.ev = self.dma.ev

    autocsr_exclude = {"ev"}
