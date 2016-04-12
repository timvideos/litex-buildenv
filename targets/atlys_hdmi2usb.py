from migen.flow.actor import *
from migen.actorlib.fifo import AsyncFIFO, SyncFIFO

from misoclib.soc import mem_decoder

from gateware.encoder import Encoder
from gateware.encoder.dma import EncoderDMAReader
from gateware.encoder.buffer import EncoderBuffer
from gateware.streamer import USBStreamer

from targets.common import *
from targets.atlys_video import VideoMixerSoC


class HDMI2USBSoC(VideoMixerSoC):
    csr_peripherals = (
        "encoder_reader",
        "encoder",
    )
    csr_map_update(VideoMixerSoC.csr_map, csr_peripherals)
    mem_map = {
        "encoder": 0x60000000,  # (shadow @0xe0000000)
    }
    mem_map.update(VideoMixerSoC.mem_map)

    def __init__(self, platform, **kwargs):
        VideoMixerSoC.__init__(self, platform, **kwargs)

        lasmim = self.sdram.crossbar.get_master()
        self.submodules.encoder_reader = EncoderDMAReader(lasmim)
        self.submodules.encoder_cdc = RenameClockDomains(AsyncFIFO([("data", 128)], 4),
                                          {"write": "sys", "read": "encoder"})
        self.submodules.encoder_buffer = RenameClockDomains(EncoderBuffer(), "encoder")
        self.submodules.encoder_fifo = RenameClockDomains(SyncFIFO(EndpointDescription([("data", 16)], packetized=True), 16), "encoder")
        self.submodules.encoder = Encoder(platform)
        self.submodules.usb_streamer = USBStreamer(platform, platform.request("fx2"))

        self.comb += [
            platform.request("user_led", 0).eq(self.encoder_reader.source.stb),
            platform.request("user_led", 1).eq(self.encoder_reader.source.ack),
            Record.connect(self.encoder_reader.source, self.encoder_cdc.sink),
            Record.connect(self.encoder_cdc.source, self.encoder_buffer.sink),
            Record.connect(self.encoder_buffer.source, self.encoder_fifo.sink),
            Record.connect(self.encoder_fifo.source, self.encoder.sink),
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
