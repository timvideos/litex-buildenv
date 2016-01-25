from migen.fhdl.std import *
from migen.sim.generic import run_simulation
from migen.flow.actor import EndpointDescription

from misoclib.mem.sdram.frontend import dma_lasmi

from gateware.encoder.dma import EncoderDMAReader
from gateware.csc.test.common import *

from misoclib.mem.sdram.module import MT48LC4M16
from misoclib.mem.sdram.phy.simphy import SDRAMPHYSim
from misoclib.mem.sdram.core import SDRAMCore
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings

from misoclib.mem import sdram


class TB(Module):
    def __init__(self):
        # sdram
        sdram_module = MT48LC4M16(75*1000000)
        sdram_phy_settings = sdram.PhySettings(
            memtype="SDR",
            dfi_databits=1*16,
            nphases=1,
            rdphase=0,
            wrphase=0,
            rdcmdphase=0,
            wrcmdphase=0,
            cl=2,
            read_latency=4,
            write_latency=0
        )
        self.submodules.sdram_phy = SDRAMPHYSim(sdram_module, sdram_phy_settings)
        self.submodules.sdram_core = SDRAMCore(self.sdram_phy,
                                               sdram_module.geom_settings,
                                               sdram_module.timing_settings,
                                               LASMIconSettings(with_refresh=False))
        
        # dma writer
        self.submodules.dma_writer = dma_lasmi.Writer(self.sdram_core.crossbar.get_master())

        # dma reader
        self.submodules.dma_reader = EncoderDMAReader(self.sdram_core.crossbar.get_master())
        self.comb += self.dma_reader.source.ack.eq(1)

    def check_line(self, value, x, y, memory_data):
        line = memory_data[16*y + x: 16*y + x + 8]
        reference = 0
        for i in range(128//16):
            reference |= (line[::-1][i] << 16*i)
        if value != reference:
            print("x:%d, y:%d "%(x, y))
            print("v %32x" %(value))
            print("l %32x" %(reference))
        return value == reference

    def gen_simulation(self, selfp):
        selfp.sdram_core.dfii._control.storage = 1
        for i in range(16):
            yield

        # write (init memory)
        memory_data = [randn(2**16) for i in range(16*16)] # 16x16 pixels = 4 macroblocks
        for i, value in enumerate(memory_data):
            selfp.dma_writer.address_data.stb = 1
            selfp.dma_writer.address_data.a = i
            selfp.dma_writer.address_data.d = memory_data[i]
            yield
            while selfp.dma_writer.address_data.ack == 0:
                yield
            selfp.dma_writer.address_data.stb = 0
            yield

        # read
        selfp.dma_reader.base.storage = 0
        selfp.dma_reader.h_width.storage = 16
        selfp.dma_reader.v_width.storage = 16
        yield
        selfp.dma_reader.start.r = 1
        selfp.dma_reader.start.re = 1
        yield
        selfp.dma_reader.start.r = 0
        selfp.dma_reader.start.re = 0

        errors = 0
        x_indexs = [0]*8 + [8]*8 + \
                   [0]*8 + [8]*8 
        y_indexs = [i for i in range(8)] + [i for i in range(8)] + \
                   [i + 8 for i in range(8)] + [i + 8 for i in range(8)] 
        for i in range(len(memory_data)*16//128):
            yield
            while selfp.dma_reader.source.stb == 0:
                yield
            x = x_indexs[i]
            y = y_indexs[i]
            errors += not self.check_line(selfp.dma_reader.source.data, x, y, memory_data)
        print("errors : {}".format(errors))

if __name__ == "__main__":
    run_simulation(TB(), ncycles=2048, vcd_name="my.vcd", keep_files=True)
