#!/usr/bin/env python3

from nexys_base import *

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


        self.specials += Instance("TDMS_encoder",
                i_clk=pixel_clk,
                i_data=vga_blue,
                i_c=Cat(vga_hsync, vga_vsync),
                i_blank=vga_blank,
                o_encoded=c0_tmds_symbol
        )

        self.specials += Instance("TDMS_encoder",
                i_clk=pixel_clk,
                i_data=vga_green,
                i_c=0,
                i_blank=vga_blank,
                o_encoded=c1_tmds_symbol
        )

        self.specials += Instance("TDMS_encoder",
                i_clk=pixel_clk,
                i_data=vga_red,
                i_c=0,
                i_blank=vga_blank,
                o_encoded=c2_tmds_symbol
        )

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

