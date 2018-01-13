from litevideo.output import VideoOut
from litedram.common import LiteDRAMPort

#from targets.netv2.pcie import SoC as BaseSoC
from targets.netv2.base import SoC as BaseSoC


class VideoOutSoC(BaseSoC):
    csr_map = {
        "hdmi_out0": 26
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        # # #

        mode = "ycbcr422"

        if mode == "ycbcr422":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=16, cd="pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "ycbcr422")
        elif mode == "rgb":
            hdmi_out0_dram_port = self.sdram.crossbar.get_port(mode="read", dw=32, cd="pix", reverse=True)
            self.submodules.hdmi_out0 = VideoOut(platform.device,
                                                 platform.request("hdmi_out"),
                                                 hdmi_out0_dram_port,
                                                 "rgb")

        self.platform.add_period_constraint(self.crg.cd_sys.clk, 10.0)
        self.platform.add_period_constraint(self.hdmi_out0.driver.clocking.cd_pix.clk, 10.0)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk)

        for name, value in sorted(self.platform.hdmi_infos.items()):
            self.add_constant(name, value)


SoC = VideoOutSoC
