from migen import *

from targets.netv2.net import SoC as BaseSoC

from litex.soc.cores.freqmeter import FreqMeter

from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from targets.utils import period_ns, csr_map_update


class VideoSoC(BaseSoC):
    csr_peripherals = [
        "hdmi_out0",
        "hdmi_in0",
        "hdmi_in0_freq",
        "hdmi_in0_edid_mem",
    ]
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        sys_clk_freq = int(100e6)

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


SoC = VideoSoC
