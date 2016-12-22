from litex.gen.fhdl.decorators import ClockDomainsRenamer
from litex.gen.fhdl.specials import Keep
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

        self.submodules.encoder_reader = EncoderDMAReader(self.sdram.crossbar.get_port())
        self.submodules.encoder_cdc = ClockDomainsRenamer({"write": "sys", "read": "encoder"})(stream.AsyncFIFO([("data", 128)], 4))
        self.submodules.encoder_buffer = ClockDomainsRenamer("encoder")(EncoderBuffer())
        self.submodules.encoder = Encoder(platform)
        fx2_pads = platform.request("fx2")
        self.submodules.encoder_streamer = USBStreamer(platform, fx2_pads)

        self.comb += [
            self.encoder_reader.source.connect(self.encoder_cdc.sink),
            self.encoder_cdc.source.connect(self.encoder_buffer.sink),
            self.encoder_buffer.source.connect(self.encoder.sink),
            self.encoder.source.connect(self.encoder_streamer.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"] + self.shadow_base, 0x2000)

        self.platform.add_period_constraint(self.encoder_streamer.cd_usb.clk, 10.0)

        self.specials += Keep(self.encoder_streamer.cd_usb.clk)
        self.specials += Keep(self.crg.cd_encoder.clk)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.crg.cd_encoder.clk,
            self.encoder_streamer.cd_usb.clk)


SoC = HDMI2USBSoC
