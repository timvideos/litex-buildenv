from migen import *

from litepcie.phy.s7pciephy import S7PCIEPHY
from litepcie.core import LitePCIeEndpoint, LitePCIeMSI
from litepcie.frontend.dma import LitePCIeDMA
from litepcie.frontend.wishbone import LitePCIeWishboneBridge

from litex.build.tools import write_to_file

from targets.netv2.base import BaseSoC
from targets.common import cpu_interface


class PCIeDMASoC(BaseSoC):
    csr_map = {
        "pcie_phy": 22,
        "dma":      23,
        "msi":      24,
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "dma_writer": 0,
        "dma_reader": 1,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    BaseSoC.mem_map["csr"] = 0x00000000
    BaseSoC.mem_map["rom"] = 0x20000000

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, csr_data_width=32, **kwargs)

        # pcie phy
        self.submodules.pcie_phy = S7PCIEPHY(platform, platform.request("pcie_x1"))
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.pcie_phy.cd_pcie.clk)

        # pcie endpoint
        self.submodules.pcie_endpoint = LitePCIeEndpoint(self.pcie_phy, with_reordering=True)

        # pcie wishbone bridge
        self.submodules.pcie_wishbone = LitePCIeWishboneBridge(self.pcie_endpoint, lambda a: 1)
        self.add_wb_master(self.pcie_wishbone.wishbone)

        # pcie dma
        self.submodules.dma = LitePCIeDMA(self.pcie_phy, self.pcie_endpoint, with_loopback=True)
        self.dma.source.connect(self.dma.sink)

        # pcie msi
        self.submodules.msi = LitePCIeMSI()
        self.comb += self.msi.source.connect(self.pcie_phy.msi)
        self.interrupts = {
            "dma_writer":    self.dma.writer.irq,
            "dma_reader":    self.dma.reader.irq
        }
        for k, v in sorted(self.interrupts.items()):
            self.comb += self.msi.irqs[self.interrupt_map[k]].eq(v)

        # flash the led on pcie clock
        counter = Signal(32)
        self.sync.clk125 += counter.eq(counter + 1)
        self.comb += platform.request("user_led", 0).eq(counter[26])
        ## pcie led
        #pcie_counter = Signal(32)
        #self.sync.pcie += pcie_counter.eq(pcie_counter + 1)
        #self.comb += self.pcie_led.eq(pcie_counter[26])


SoC = PCIeDMASoC
