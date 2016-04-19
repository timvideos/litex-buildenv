#!/usr/bin/env python3

from nexys_base import *

from litevideo.output.hdmi.encoder import Encoder

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

        c0_tmds_symbol = Signal(10)
        c1_tmds_symbol = Signal(10)
        c2_tmds_symbol = Signal(10)


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
        self.comb += self.cd_pix.clk.eq(pixel_clk)

        # # #

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

        # # #

        hdmi_tx_clk = Signal()
        hdmi_tx = Signal(3)

        class Serializer(Module):
            def __init__(self, data, serial):
                shift1 = Signal()
                shift2 = Signal()
                ce_delay = Signal()

                self.sync.pix += ce_delay.eq(~reset)

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

                    o_OQ=serial,
                    i_CLK=pixel_clk_x5,
                    i_CLKDIV=pixel_clk,
                    i_D1=data[0],
                    i_D2=data[1],
                    i_D3=data[2],
                    i_D4=data[3],
                    i_D5=data[4],
                    i_D6=data[5],
                    i_D7=data[6],
                    i_D8=data[7],
                    i_OCE=ce_delay,
                    i_RST=reset,

                    i_SHIFTIN1=shift1,
                    i_SHIFTIN2=shift2,
                    i_T1=0,
                    i_T2=0,
                    i_T3=0,
                    i_T4=0,
                    i_TBYTEIN=0,
                    i_TCE=0
                )

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

                    i_CLK=pixel_clk_x5,
                    i_CLKDIV=pixel_clk,

                    o_SHIFTOUT1=shift1,
                    o_SHIFTOUT2=shift2,

                    i_D1=0,
                    i_D2=0,
                    i_D3=data[8],
                    i_D4=data[9],
                    i_D5=0,
                    i_D6=0,
                    i_D7=0,
                    i_D8=0,
                    i_OCE=ce_delay,
                    i_RST=reset,

                    i_SHIFTIN1=0,
                    i_SHIFTIN2=0,
                    i_T1=0,
                    i_T2=0,
                    i_T3=0,
                    i_T4=0,
                    i_TBYTEIN=0,
                    i_TCE=0
                )

        self.submodules.c0_serializer = Serializer(c0_tmds_symbol, hdmi_tx[0])
        self.submodules.c1_serializer = Serializer(c1_tmds_symbol, hdmi_tx[1])
        self.submodules.c2_serializer = Serializer(c2_tmds_symbol, hdmi_tx[2])
        self.submodules.clk_serializer = Serializer(Signal(10, reset=0b0000011111), hdmi_tx_clk)

        # # #

        self.specials += [
            Instance("OBUFDS",
                p_IOSTANDARD="TDMS_33", p_SLEW="FAST",
                i_I=hdmi_tx_clk, o_O=pads.clk_p, o_OB=pads.clk_n),
            Instance("OBUFDS",
                p_IOSTANDARD="TDMS_33", p_SLEW="FAST",
                i_I=hdmi_tx[0], o_O=pads.data0_p, o_OB=pads.data0_n),
            Instance("OBUFDS",
                p_IOSTANDARD="TDMS_33", p_SLEW="FAST",
                i_I=hdmi_tx[1], o_O=pads.data1_p, o_OB=pads.data1_n),
            Instance("OBUFDS",
                p_IOSTANDARD="TDMS_33", p_SLEW="FAST",
                i_I=hdmi_tx[2], o_O=pads.data2_p, o_OB=pads.data2_n)
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

