#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.encoder import Encoder

class VideoOutSoC(BaseSoC):
    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")

        pixel_clk = Signal()
        pixel_clk_x5 = Signal()
        reset = Signal()

        vga_hsync = Signal()
        vga_vsync = Signal()
        vga_red = Signal(8)
        vga_green = Signal(8)
        vga_blue = Signal(8)
        vga_blank = Signal()

        c0_tmds_symbol = Signal(10)
        c1_tmds_symbol = Signal(10)
        c2_tmds_symbol = Signal(10)

        self.specials += Instance("top_level",
                i_clk100=self.crg.clk100,

                o_pixel_clk=pixel_clk,
                o_pixel_clk_x5=pixel_clk_x5,
                o_reset=reset,

                o_vga_hsync=vga_hsync,
                o_vga_vsync=vga_vsync,
                o_vga_red=vga_red,
                o_vga_green=vga_green,
                o_vga_blue=vga_blue,
                o_vga_blank=vga_blank,
        )

        self.clock_domains.cd_pix = ClockDomain("pix")
        self.comb += self.cd_pix.clk.eq(pixel_clk)

        c0_encoder = ClockDomainsRenamer("pix")(Encoder())
        self.submodules += c0_encoder
        self.comb += [
            c0_encoder.d.eq(vga_blue),
            c0_encoder.c.eq(Cat(vga_hsync, vga_vsync)),
            c0_encoder.de.eq(~vga_blank),
            c0_tmds_symbol.eq(c0_encoder.out)
        ]

        c1_encoder = ClockDomainsRenamer("pix")(Encoder())
        self.submodules += c1_encoder
        self.comb += [
            c1_encoder.d.eq(vga_green),
            c1_encoder.c.eq(0),
            c1_encoder.de.eq(~vga_blank),
            c1_tmds_symbol.eq(c1_encoder.out)
        ]

        c2_encoder = ClockDomainsRenamer("pix")(Encoder())
        self.submodules += c2_encoder
        self.comb += [
            c2_encoder.d.eq(vga_red),
            c2_encoder.c.eq(0),
            c2_encoder.de.eq(~vga_blank),
            c2_tmds_symbol.eq(c2_encoder.out)
        ]

        self.specials += Instance("vga_to_hdmi",
            i_pixel_clk=pixel_clk,
            i_pixel_clk_x5=pixel_clk_x5,
            i_reset=reset,

            i_c0_tmds_symbol=c0_tmds_symbol,
            i_c1_tmds_symbol=c1_tmds_symbol,
            i_c2_tmds_symbol=c2_tmds_symbol,

            o_hdmi_tx_rscl=pads.scl,
            io_hdmi_tx_rsda=pads.sda,
            i_hdmi_tx_hpd=pads.hdp,
            io_hdmi_tx_cec=pads.cec,

            o_hdmi_tx_clk_p=pads.clk_p,
            o_hdmi_tx_clk_n=pads.clk_n,
            o_hdmi_tx_p=Cat(pads.data0_p, pads.data1_p, pads.data2_p),
            o_hdmi_tx_n=Cat(pads.data0_n, pads.data1_n, pads.data2_n)
        )

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

