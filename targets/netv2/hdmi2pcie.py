from migen import *

from targets.netv2.video import SoC as BaseSoC

from litex.soc.interconnect import wishbone
from litex.soc.cores.freqmeter import FreqMeter

from litepcie.phy.s7pciephy import S7PCIEPHY
from litepcie.core import LitePCIeEndpoint, LitePCIeMSI
from litepcie.frontend.dma import LitePCIeDMA
from litepcie.frontend.wishbone import LitePCIeWishboneBridge

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from targets.utils import period_ns, csr_map_update

class WishboneEndianSwap(Module):
    def __init__(self, wb_if):
        self.wishbone = wishbone.Interface()
        self.sync += [
            self.wishbone.adr.eq(wb_if.adr),

            self.wishbone.dat_w[0:8].eq(wb_if.dat_w[24:32]),
            self.wishbone.dat_w[8:16].eq(wb_if.dat_w[16:24]),
            self.wishbone.dat_w[16:24].eq(wb_if.dat_w[8:16]),
            self.wishbone.dat_w[24:32].eq(wb_if.dat_w[0:8]),
            #self.wishbone.dat_w.eq(wb_if.dat_w),

            wb_if.dat_r[0:8].eq(self.wishbone.dat_r[24:32]),
            wb_if.dat_r[8:16].eq(self.wishbone.dat_r[16:24]),
            wb_if.dat_r[16:24].eq(self.wishbone.dat_r[8:16]),
            wb_if.dat_r[24:32].eq(self.wishbone.dat_r[0:8]),
            #wb_if.dat_r.eq(self.wishbone.dat_r),

            self.wishbone.sel[3].eq(wb_if.sel[0]),
            self.wishbone.sel[2].eq(wb_if.sel[1]),
            self.wishbone.sel[1].eq(wb_if.sel[2]),
            self.wishbone.sel[0].eq(wb_if.sel[3]),
            #self.wishbone.sel.eq(wb_if.sel),

            self.wishbone.cyc.eq(wb_if.cyc),
            self.wishbone.stb.eq(wb_if.stb),
            wb_if.ack.eq(self.wishbone.ack),
            self.wishbone.we.eq(wb_if.we),
            self.wishbone.cti.eq(wb_if.cti),
            self.wishbone.bte.eq(wb_if.bte),
            wb_if.err.eq(self.wishbone.err),
        ]


class HDMI2PCIeSoC(BaseSoC):
    csr_peripherals = [
        "pcie_phy",
        "pcie_dma0",
        "pcie_dma1",
        "pcie_msi",
    ]
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, csr_data_width=32, *args, **kwargs)

        sys_clk_freq = int(100e6)

        # pcie phy
        self.submodules.pcie_phy = S7PCIEPHY(platform, platform.request("pcie_x1"), bar0_size=32*1024*1024)
        platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.pcie_phy.cd_pcie.clk)

        # pcie endpoint
        self.submodules.pcie_endpoint = LitePCIeEndpoint(self.pcie_phy)

        # pcie wishbone bridge
        self.submodules.pcie_bridge = LitePCIeWishboneBridge(self.pcie_endpoint, lambda a: 1, shadow_base=0x44000000)
        self.submodules.wb_swap = WishboneEndianSwap(self.pcie_bridge.wishbone)
        self.add_wb_master(self.wb_swap.wishbone)

        # pcie dma
        self.submodules.pcie_dma0 = LitePCIeDMA(self.pcie_phy, self.pcie_endpoint, with_loopback=True)

        # pcie msi
        self.submodules.pcie_msi = LitePCIeMSI()
        self.comb += self.pcie_msi.source.connect(self.pcie_phy.msi)
        self.interrupts = {
            "PCIE_DMA0_WRITER":    self.pcie_dma0.writer.irq,
            "PCIE_DMA0_READER":    self.pcie_dma0.reader.irq
        }
        for i, (k, v) in enumerate(sorted(self.interrupts.items())):
            self.comb += self.pcie_msi.irqs[i].eq(v)
            self.add_constant(k + "_INTERRUPT", i)


SoC = HDMI2PCIeSoC
