from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from gateware import freq_measurement
from gateware import i2c

from targets.utils import csr_map_update, period_ns
from targets.opsis.net import NetSoC as BaseSoC


class VideoSoC(BaseSoC):
    csr_peripherals = (
        "hdmi_out0",
        "hdmi_out1",
        "hdmi_in0",
        "hdmi_in0_freq",
        "hdmi_in0_edid_mem",
        "hdmi_in1",
        "hdmi_in1_freq",
        "hdmi_in1_edid_mem",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        mode = "ycbcr422"
        if mode == "ycbcr422":
            dw = 16
        elif mode == "rgb":
            dw = 32
        else:
            raise SystemError("Unknown pixel mode.")

        # hdmi in 0
        hdmi_in0_pads = platform.request("hdmi_in", 0)

        self.submodules.hdmi_in0 = HDMIIn(
            hdmi_in0_pads,
            self.sdram.crossbar.get_port(mode="write"),
            fifo_depth=512,
            )

        self.submodules.hdmi_in0_freq = freq_measurement.FrequencyMeasurement(
            self.hdmi_in0.clocking.clk_input, measure_period=self.clk_freq)

        # hdmi in 1
        hdmi_in1_pads = platform.request("hdmi_in", 1)

        self.submodules.hdmi_in1 = HDMIIn(
            hdmi_in1_pads,
            self.sdram.crossbar.get_port(mode="write"),
            fifo_depth=512,
        )

        self.submodules.hdmi_in1_freq = freq_measurement.FrequencyMeasurement(
            self.hdmi_in1.clocking.clk_input, measure_period=self.clk_freq)



        # hdmi out 0
        hdmi_out0_pads = platform.request("hdmi_out", 0)

        hdmi_out0_dram_port = self.sdram.crossbar.get_port(
            mode="read",
            data_width=dw,
            clock_domain="hdmi_out0_pix",
            reverse=True,
        )

        self.submodules.hdmi_out0 = VideoOut(
            platform.device,
            hdmi_out0_pads,
            hdmi_out0_dram_port,
            mode=mode,
            fifo_depth=4096,
        )

        self.hdmi_out0.submodules.i2c = i2c.I2C(hdmi_out0_pads)

        # hdmi out 1 : Share clocking with hdmi_out0 since no PLL_ADV left.
        hdmi_out1_pads = platform.request("hdmi_out", 1)

        hdmi_out1_dram_port = self.sdram.crossbar.get_port(
            mode="read",
            data_width=dw,
            clock_domain="hdmi_out1_pix",
            reverse=True,
        )

        self.submodules.hdmi_out1 = VideoOut(
            platform.device,
            hdmi_out1_pads,
            hdmi_out1_dram_port,
            mode=mode,
            fifo_depth=4096,
            external_clocking=self.hdmi_out0.driver.clocking,
        )

        self.hdmi_out1.submodules.i2c = i2c.I2C(hdmi_out1_pads)

        # all PLL_ADV are used: router needs help...
        platform.add_platform_command("""INST crg_pll_adv LOC=PLL_ADV_X0Y0;""")
        # FIXME: Fix the HDMI out so this can be removed.
        platform.add_platform_command(
            """PIN "hdmi_out_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command(
            """PIN "hdmi_out_pix_bufg_1.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        # We have CDC to go from sys_clk to pixel domain
        platform.add_platform_command(
            """
NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
NET "{pix1_clk}" TNM_NET = "GRPpix1_clk";
""",
                pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk,
                pix1_clk=self.hdmi_out1.driver.clocking.cd_pix.clk,
        )
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk,
            self.hdmi_out1.driver.clocking.cd_pix.clk)

        for name, value in sorted(self.platform.hdmi_infos.items()):
            self.add_constant(name, value)

        self.add_interrupt("hdmi_in0")
        self.add_interrupt("hdmi_in1")


SoC = VideoSoC
