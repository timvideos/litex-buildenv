#!/usr/bin/env python3
from netv2_base import *

from litepcie.phy.s7pciephy import S7PCIEPHY
from litepcie.core import LitePCIeEndpoint, LitePCIeMSI
from litepcie.frontend.dma import LitePCIeDMA
from litepcie.frontend.wishbone import LitePCIeWishboneBridge

from litex.build.tools import write_to_file

import cpu_interface


class PCIeDMASoC(BaseSoC):
    csr_map = {
        "pcie_phy": 20,
        "dma":      21,
        "msi":      22,
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "dma_writer": 0,
        "dma_reader": 1,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        # pcie phy
        self.submodules.pcie_phy = S7PCIEPHY(platform, link_width=1, bar0_size=0x80000000, cd="sys")

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
        self.comb += self.msi.source.connect(self.pcie_phy.interrupt)
        self.interrupts = {
            "dma_writer":    self.dma.writer.irq,
            "dma_reader":    self.dma.reader.irq
        }
        for k, v in sorted(self.interrupts.items()):
            self.comb += self.msi.irqs[self.interrupt_map[k]].eq(v)


def main():
    parser = argparse.ArgumentParser(description="NeTV2 LiteX PCIe SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    platform = netv2.Platform()
    soc = PCIeDMASoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build")
    vns = builder.build()

    csr_header = cpu_interface.get_csr_header(soc.get_csr_regions(), soc.get_constants())
    write_to_file(os.path.join("software", "pcie", "kernel", "csr.h"), csr_header)

if __name__ == "__main__":
    main()
