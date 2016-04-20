#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.s7 import S7HDMIOutClocking
from litevideo.output.hdmi.s7 import S7HDMIOutEncoderSerializer
from litevideo.output.hdmi.s7 import S7HDMIOutPHY


class VideoOutSoC(BaseSoC):
    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")
        self.comb += pads.scl.eq(1)

        vga_hsync = Signal()
        vga_vsync = Signal()
        vga_red = Signal(8)
        vga_green = Signal(8)
        vga_blue = Signal(8)
        vga_blank = Signal()

        # # #


        self.specials += Instance("vga_gen",
                i_pixel_clk=ClockSignal("pix"),

                o_vga_hsync=vga_hsync,
                o_vga_vsync=vga_vsync,
                o_vga_red=vga_red,
                o_vga_green=vga_green,
                o_vga_blue=vga_blue,
                o_vga_blank=vga_blank,
        )

        self.submodules.hdmi_clocking = S7HDMIOutClocking(self.crg.clk100)
        self.submodules.hdmi_phy = S7HDMIOutPHY(pads)
        self.comb += [
            self.hdmi_phy.hsync.eq(vga_hsync),
            self.hdmi_phy.vsync.eq(vga_vsync),
            self.hdmi_phy.de.eq(~vga_blank),
            self.hdmi_phy.r.eq(vga_red),
            self.hdmi_phy.g.eq(vga_green),
            self.hdmi_phy.b.eq(vga_blue)
        ]
        self.submodules.clk_es = S7HDMIOutEncoderSerializer(pads.clk_p, pads.clk_n, bypass_encoder=True)
        self.comb += self.clk_es.data.eq(Signal(10, reset=0b0000011111))

        # # #

        platform.add_source_dir(os.path.join("gateware", "hdmi_out"))


def main():
    parser = argparse.ArgumentParser(description="Nexys LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = nexys.Platform()
    soc = VideoOutSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()

