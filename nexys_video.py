#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.s7 import S7HDMIOutEncoderSerializer, S7HDMIOutPHY


class VideoOutSoC(BaseSoC):
    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")
        self.comb += pads.scl.eq(1)

        pixel_clk = Signal()
        pixel_clk_x5 = Signal()
        reset = Signal()

        vga_hsync = Signal()
        vga_vsync = Signal()
        vga_red = Signal(8)
        vga_green = Signal(8)
        vga_blue = Signal(8)
        vga_blank = Signal()

        # # #

        mmcm_locked = Signal()
        mmcm_fb = Signal()

        self.specials += Instance("MMCME2_BASE",
                     p_BANDWIDTH="OPTIMIZED", i_RST=0, o_LOCKED=mmcm_locked,

                     # VCO
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT_F=30.0, p_CLKFBOUT_PHASE=0.000, p_DIVCLK_DIVIDE=4,
                     i_CLKIN1=self.crg.clk100, i_CLKFBIN=mmcm_fb, o_CLKFBOUT=mmcm_fb,

                     # CLK0
                     p_CLKOUT0_DIVIDE_F=5.0, p_CLKOUT0_PHASE=0.000, o_CLKOUT0=pixel_clk,
                     # CLK1
                     p_CLKOUT1_DIVIDE=1, p_CLKOUT1_PHASE=0.000, o_CLKOUT1=pixel_clk_x5,
        )
        self.comb += reset.eq(~mmcm_locked)

        # # #

        self.specials += Instance("vga_gen",
                i_pixel_clk=pixel_clk,

                o_vga_hsync=vga_hsync,
                o_vga_vsync=vga_vsync,
                o_vga_red=vga_red,
                o_vga_green=vga_green,
                o_vga_blue=vga_blue,
                o_vga_blank=vga_blank,
        )

        self.clock_domains.cd_pix = ClockDomain("pix")
        self.clock_domains.cd_pix5x = ClockDomain("pix5x", reset_less=True)
        self.comb += [
            self.cd_pix.clk.eq(pixel_clk),
            self.cd_pix.rst.eq(reset),
            self.cd_pix5x.clk.eq(pixel_clk_x5)
        ]

        self.submodules.hdmi_out_phy = S7HDMIOutPHY(pads)
        self.comb += [
            self.hdmi_out_phy.hsync.eq(vga_hsync),
            self.hdmi_out_phy.vsync.eq(vga_vsync),
            self.hdmi_out_phy.de.eq(~vga_blank),
            self.hdmi_out_phy.r.eq(vga_red),
            self.hdmi_out_phy.g.eq(vga_green),
            self.hdmi_out_phy.b.eq(vga_blue)
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

