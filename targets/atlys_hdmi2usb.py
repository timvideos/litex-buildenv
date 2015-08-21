from targets.atlys_base import *
from targets.atlys_base import default_subtarget as opsis_base_soc

from hdl import dvisampler
from hdl import framebuffer

from hdl.encoder import EncoderReader, Encoder
from hdl.streamer import USBStreamer

class VideomixerSoC(opsis_base_soc):
    csr_map = {
        "fb0":                  19,
        "fb1":                  20,
        "dvisampler0":          21,
        "dvisampler0_edid_mem": 22,
        "dvisampler1":          23,
        "dvisampler1_edid_mem": 24,
    }
    csr_map.update(opsis_base_soc.csr_map)

    interrupt_map = {
        "dvisampler0": 3,
        "dvisampler1": 4,
    }
    interrupt_map.update(opsis_base_soc.interrupt_map)

    def __init__(self, platform, **kwargs):
        opsis_base_soc.__init__(self, platform, **kwargs)
        self.submodules.dvisampler0 = dvisampler.DVISampler(platform.request("dvi_in", 0),
                                                           self.sdram.crossbar.get_master(),
                                                           fifo_depth=1024)
        self.submodules.dvisampler1 = dvisampler.DVISampler(platform.request("dvi_in", 1),
                                                           self.sdram.crossbar.get_master(),
                                                           fifo_depth=1024)
        self.submodules.fb0 = framebuffer.Framebuffer(None, platform.request("dvi_out", 0),
                                                     self.sdram.crossbar.get_master())
        self.submodules.fb1 = framebuffer.Framebuffer(None, platform.request("dvi_out", 1),
                                                     self.sdram.crossbar.get_master(),
                                                     self.fb0.driver.clocking) # share clocking with frambuffer0
                                                                               # since no PLL_ADV left.

        platform.add_platform_command("""INST PLL_ADV LOC=PLL_ADV_X0Y0;""") # all PLL_ADV are used: router needs help...
        platform.add_platform_command("""PIN "dviout_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command("""PIN "BUFG_8.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command("""
NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
NET "{pix1_clk}" TNM_NET = "GRPpix1_clk";
TIMESPEC "TSise_sucks7" = FROM "GRPpix0_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks8" = FROM "GRPsys_clk" TO "GRPpix0_clk" TIG;
TIMESPEC "TSise_sucks9" = FROM "GRPpix1_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks10" = FROM "GRPsys_clk" TO "GRPpix1_clk" TIG;
""", pix0_clk=self.fb0.driver.clocking.cd_pix.clk,
     pix1_clk=self.fb1.driver.clocking.cd_pix.clk,
)


class HDMI2USBSoC(VideomixerSoC):
    csr_map = {
        "encoder_reader": 25,
        "encoder":        26
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
            platform.request("user_led", 0).eq(self.encoder_reader.source.stb),
            platform.request("user_led", 1).eq(self.encoder_reader.source.ack),
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
