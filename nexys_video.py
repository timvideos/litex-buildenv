#!/usr/bin/env python3

from nexys_base import *

class VideoOutSoC(MiniSoC):
    def __init__(self, platform, *args, **kwargs):
        MiniSoC.__init__(self, platform, *args, **kwargs)

        pads = platform.request("hdmi_out")

        self.specials += Instance("top_level",
                i_clk100=self.crg.clk100,

                o_hdmi_tx_rscl=pads.scl,
                io_hdmi_tx_rsda=pads.sda,
                i_hdmi_tx_hpd=pads.hdp,
                io_hdmi_tx_cec=pads.cec,

                o_hdmi_tx_clk_p=pads.clk_p,
                o_hdmi_tx_clk_n=pads.clk_n,
                o_hdmi_tx_p=Cat(pads.data0_p, pads.data1_p, pads.data2_p),
                o_hdmi_tx_n=Cat(pads.data0_n, pads.data1_n, pads.data2_n))

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

