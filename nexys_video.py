#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.encoder import Encoder


class _S7HDMIOutEncoderSerializer(Module):
    def __init__(self, rst, pad_p, pad_n):
        self.submodules.encoder = ClockDomainsRenamer("pix")(Encoder())
        self.d, self.c, self.de = self.encoder.d, self.encoder.c, self.encoder.de

        # # #

        shift = Signal(2)
        ce = Signal()
        self.sync.pix += ce.eq(~rst)

        pad_se = Signal()

        # OSERDESE2 master
        self.specials += Instance("OSERDESE2",
            p_DATA_RATE_OQ="DDR",
            p_DATA_RATE_TQ="DDR",
            p_DATA_WIDTH=10,
            p_INIT_OQ=1,
            p_INIT_TQ=1,
            p_SERDES_MODE="MASTER",
            p_SRVAL_OQ=0,
            p_SRVAL_TQ=0,
            p_TBYTE_CTL="FALSE",
            p_TBYTE_SRC="FALSE",
            p_TRISTATE_WIDTH=1,

            o_OQ=pad_se,
            i_CLK=ClockSignal("pix5x"),
            i_CLKDIV=ClockSignal("pix"),
            i_D1=self.encoder.out[0],
            i_D2=self.encoder.out[1],
            i_D3=self.encoder.out[2],
            i_D4=self.encoder.out[3],
            i_D5=self.encoder.out[4],
            i_D6=self.encoder.out[5],
            i_D7=self.encoder.out[6],
            i_D8=self.encoder.out[7],
            i_OCE=ce,
            i_RST=rst,

            i_SHIFTIN1=shift[0],
            i_SHIFTIN2=shift[1],
            i_T1=0,
            i_T2=0,
            i_T3=0,
            i_T4=0,
            i_TBYTEIN=0,
            i_TCE=0
        )

        # OSERDESE2 slave
        self.specials += Instance("OSERDESE2",
            p_DATA_RATE_OQ="DDR",
            p_DATA_RATE_TQ="DDR",
            p_DATA_WIDTH=10,
            p_INIT_OQ=1,
            p_INIT_TQ=1,
            p_SERDES_MODE="SLAVE",
            p_SRVAL_OQ=0,
            p_SRVAL_TQ=0,
            p_TBYTE_CTL="FALSE",
            p_TBYTE_SRC="FALSE",
            p_TRISTATE_WIDTH=1,

            i_CLK=ClockSignal("pix5x"),
            i_CLKDIV=ClockSignal("pix"),

            o_SHIFTOUT1=shift[0],
            o_SHIFTOUT2=shift[1],

            i_D1=0,
            i_D2=0,
            i_D3=self.encoder.out[8],
            i_D4=self.encoder.out[9],
            i_D5=0,
            i_D6=0,
            i_D7=0,
            i_D8=0,
            i_OCE=ce,
            i_RST=rst,

            i_SHIFTIN1=0,
            i_SHIFTIN2=0,
            i_T1=0,
            i_T2=0,
            i_T3=0,
            i_T4=0,
            i_TBYTEIN=0,
            i_TCE=0
        )

        self.specials += Instance("OBUFDS",
                p_IOSTANDARD="TDMS_33", p_SLEW="FAST",
                i_I=pad_se, o_O=pad_p, o_OB=pad_n
        )


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

        self.clock_domains.cd_pix = ClockDomain("pix", reset_less=True)
        self.clock_domains.cd_pix5x = ClockDomain("pix5x", reset_less=True)
        self.comb += [
            self.cd_pix.clk.eq(pixel_clk),
            self.cd_pix5x.clk.eq(pixel_clk_x5)
        ]

        self.submodules.c0_es  = _S7HDMIOutEncoderSerializer(reset, pads.data0_p, pads.data0_n)
        self.submodules.c1_es  = _S7HDMIOutEncoderSerializer(reset, pads.data1_p, pads.data1_n)
        self.submodules.c2_es  = _S7HDMIOutEncoderSerializer(reset, pads.data2_p, pads.data2_n)
        self.submodules.clk_es = _S7HDMIOutEncoderSerializer(reset, pads.clk_p, pads.clk_n)
        self.comb += [
            self.c0_es.d.eq(vga_blue),
            self.c0_es.c.eq(Cat(vga_hsync, vga_vsync)),
            self.c0_es.de.eq(~vga_blank),

            self.c1_es.d.eq(vga_green),
            self.c1_es.c.eq(0),
            self.c1_es.de.eq(~vga_blank),

            self.c2_es.d.eq(vga_red),
            self.c2_es.c.eq(0),
            self.c2_es.de.eq(~vga_blank),

            self.clk_es.d.eq(Signal(10, reset=0b0000011111)),
            self.clk_es.c.eq(0),
            self.clk_es.de.eq(~vga_blank)
        ]

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

