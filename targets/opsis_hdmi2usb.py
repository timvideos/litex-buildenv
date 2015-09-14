from targets.opsis_base import *
from targets.opsis_base import default_subtarget as opsis_base_soc

from hdl.hdmi_in import HDMIIn
from hdl.hdmi_out import HDMIOut
from hdl.encoder import EncoderReader, Encoder
from hdl.streamer import USBStreamer

class VideomixerSoC(opsis_base_soc):
    csr_map = {
        "hdmi_out0":         20,
        "hdmi_out1":         21,
        "hdmi_in0":          22,
        "hdmi_in0_edid_mem": 23,
        "hdmi_in1":          24,
        "hdmi_in1_edid_mem": 25,
    }
    csr_map.update(opsis_base_soc.csr_map)

    interrupt_map = {
        "hdmi_in0": 3,
        "hdmi_in1": 4,
    }
    interrupt_map.update(opsis_base_soc.interrupt_map)

    def __init__(self, platform, **kwargs):
        opsis_base_soc.__init__(self, platform, **kwargs)
        self.submodules.hdmi_in0 = HDMIIn(platform.request("hdmi_in", 0),
                                          self.sdram.crossbar.get_master(),
                                          fifo_depth=512)
        self.submodules.hdmi_in1 = HDMIIn(platform.request("hdmi_in", 1),
                                          self.sdram.crossbar.get_master(),
                                          fifo_depth=512)
        self.submodules.hdmi_out0 = HDMIOut(platform.request("hdmi_out", 0),
                                            self.sdram.crossbar.get_master())
        self.submodules.hdmi_out1 = HDMIOut(platform.request("hdmi_out", 1),
                                            self.sdram.crossbar.get_master(),
                                            self.hdmi_out0.driver.clocking) # share clocking with hdmi_out0
                                                                            # since no PLL_ADV left.

        platform.add_platform_command("""INST PLL_ADV LOC=PLL_ADV_X0Y0;""") # all PLL_ADV are used: router needs help...
        platform.add_platform_command("""PIN "hdmi_out_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command("""PIN "hdmi_out_pix_bufg_1.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command("""
NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
NET "{pix1_clk}" TNM_NET = "GRPpix1_clk";
TIMESPEC "TSise_sucks7" = FROM "GRPpix0_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks8" = FROM "GRPsys_clk" TO "GRPpix0_clk" TIG;
TIMESPEC "TSise_sucks9" = FROM "GRPpix1_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks10" = FROM "GRPsys_clk" TO "GRPpix1_clk" TIG;
""", pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk,
     pix1_clk=self.hdmi_out1.driver.clocking.cd_pix.clk,
)
        for k, v in platform.hdmi_infos.items():
            self.add_constant(k, v)


class HDMI2USBSoC(VideomixerSoC):
    csr_map = {
        "encoder_reader": 26,
        "encoder":        27
    }
    csr_map.update(VideomixerSoC.csr_map)
    mem_map = {
        "encoder": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(VideomixerSoC.mem_map)

    def __init__(self, platform, **kwargs):
        VideomixerSoC.__init__(self, platform, **kwargs)

        self.submodules.encoder_reader = EncoderReader(self.sdram.crossbar.get_master())
        self.submodules.encoder = Encoder(platform)
        self.submodules.usb_streamer = USBStreamer(platform, platform.request("fx2"))

        self.comb += [
            Record.connect(self.encoder_reader.source, self.encoder.sink),
            Record.connect(self.encoder.source, self.usb_streamer.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"]+self.shadow_base, 0x2000)

        platform.add_platform_command("""
NET "{usb_clk}" TNM_NET = "GRPusb_clk";
TIMESPEC "TSise_sucks11" = FROM "GRPusb_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks12" = FROM "GRPsys_clk" TO "GRPusb_clk" TIG;
""", usb_clk=platform.lookup_request("fx2").ifclk)

default_subtarget = HDMI2USBSoC
