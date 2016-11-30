#!/usr/bin/env python3
from opsis_video import *

from gateware.encoder import EncoderDMAReader, Encoder
from gateware.streamer import USBStreamer

from litescope import LiteScopeAnalyzer

base_cls = VideoMixerSoC

class HDMI2USBSoC(base_cls):
    csr_peripherals = (
        "encoder_reader",
        "encoder",
        "analyzer",
    )
    csr_map_update(base_cls.csr_map, csr_peripherals)
    mem_map = {
        "encoder": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(base_cls.mem_map)

    def __init__(self, platform, **kwargs):
        base_cls.__init__(self, platform, **kwargs)

        self.submodules.encoder_reader = EncoderDMAReader(self.sdram.crossbar.get_port())
        self.submodules.encoder = Encoder(platform)
        self.submodules.encoder_streamer = USBStreamer(platform, platform.request("fx2"))

        self.comb += [
            self.encoder_reader.source.connect(self.encoder.sink),
            self.encoder.source.connect(self.encoder_streamer.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"] + self.shadow_base, 0x2000)

        self.platform.add_period_constraint(self.encoder_streamer.cd_usb.clk, 10.0) # XXX

        self.specials += Keep(self.encoder_streamer.cd_usb.clk)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.encoder_streamer.cd_usb.clk)

        analyzer_signals = [
            self.encoder.sink.data,
            self.encoder.sink.valid,
            self.encoder.sink.ready,
            self.encoder.source.data,
            self.encoder.source.valid,
            self.encoder.source.ready,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 1024)

    def do_exit(self, vns):
        self.analyzer.export_csv(vns, "test/analyzer.csv")


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = opsis_platform.Platform()
    soc = HDMI2USBSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()
    soc.do_exit(vns)

if __name__ == "__main__":
    main()
