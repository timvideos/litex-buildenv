from migen.fhdl.decorators import ClockDomainsRenamer
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.interconnect import stream

from gateware.encoder import EncoderDMAReader, EncoderBuffer, Encoder
from gateware.streamer import USBStreamer

from targets.utils import csr_map_update
from targets.atlys.video import SoC as BaseSoC


class HDMI2USBSoC(BaseSoC):
    csr_peripherals = (
        "encoder_reader",
        "encoder",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)
    mem_map = {
        "encoder": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        encoder_port = self.sdram.crossbar.get_port(
            mode="read",
            data_width=128,
            reverse=True,
        )
        self.submodules.encoder_reader = EncoderDMAReader(encoder_port)
        encoder_cdc = stream.AsyncFIFO([("data", 128)], 4)
        encoder_cdc = ClockDomainsRenamer({"write": "sys",
                                           "read": "encoder"})(encoder_cdc)
        encoder_buffer = ClockDomainsRenamer("encoder")(EncoderBuffer())
        encoder = Encoder(platform)
        encoder_streamer = USBStreamer(platform, platform.request("fx2"))
        self.submodules += encoder_cdc, encoder_buffer, encoder, encoder_streamer

        self.comb += [
            self.encoder_reader.source.connect(encoder_cdc.sink),
            encoder_cdc.source.connect(encoder_buffer.sink),
            encoder_buffer.source.connect(encoder.sink),
            encoder.source.connect(encoder_streamer.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), encoder.bus)
        self.add_memory_region("encoder",
            self.mem_map["encoder"] + self.shadow_base, 0x2000)

        self.platform.add_period_constraint(encoder_streamer.cd_usb.clk, 10.0)

        encoder_streamer.cd_usb.clk.attr.add("keep")
        self.crg.cd_encoder.clk.attr.add("keep")
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.crg.cd_encoder.clk,
            encoder_streamer.cd_usb.clk)


SoC = HDMI2USBSoC
