from migen import *

from targets.netv2.base import SoC as BaseSoC

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

        "hdmi_out0",
        "hdmi_in0",
        "hdmi_in0_freq",
        "hdmi_in0_edid_mem",
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
        self.submodules.pcie_bridge = LitePCIeWishboneBridge(self.pcie_endpoint, lambda a: 1, shadow_base=0x40000000)
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

        # hdmi in 0
        hdmi_in0_pads = platform.request("hdmi_in", 0)
        self.submodules.hdmi_in0_freq = FreqMeter(period=sys_clk_freq)
        self.submodules.hdmi_in0 = HDMIIn(
            hdmi_in0_pads,
            self.sdram.crossbar.get_port(mode="write"),
            fifo_depth=1024,
            device="xc7",
            split_mmcm=True)
        self.comb += self.hdmi_in0_freq.clk.eq(self.hdmi_in0.clocking.cd_pix.clk),
        for clk in [self.hdmi_in0.clocking.cd_pix.clk,
                    self.hdmi_in0.clocking.cd_pix1p25x.clk,
                    self.hdmi_in0.clocking.cd_pix5x.clk]:
            self.platform.add_false_path_constraints(self.crg.cd_sys.clk, clk)
        self.platform.add_period_constraint(platform.lookup_request("hdmi_in", 0).clk_p, period_ns(148.5e6))

        # hdmi out 0
        hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="hdmi_out0_pix", reverse=True)
        self.submodules.hdmi_out0 = VideoOut(
            platform.device,
            platform.request("hdmi_out", 0),
            hdmi_out0_dram_port,
            "ycbcr422",
            fifo_depth=4096)
        for clk in [self.hdmi_out0.driver.clocking.cd_pix.clk,
                    self.hdmi_out0.driver.clocking.cd_pix5x.clk]:
            self.platform.add_false_path_constraints(self.crg.cd_sys.clk, clk)

        for name, value in sorted(self.platform.hdmi_infos.items()):
            self.add_constant(name, value)

        self.add_interrupt("hdmi_in0")


SoC = HDMI2PCIeSoC
