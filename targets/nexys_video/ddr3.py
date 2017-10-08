#!/usr/bin/env python3

from nexys_base import *

from litex.soc.cores.uart import UARTWishboneBridge

from litedram.modules import MT41K256M16
from litedram.phy import a7ddrphy

from gateware import dna, xadc


class BaseSoC(SoCSDRAM):
    csr_peripherals = {
        "ddrphy",
        "dna",
        "xadc",
        "analyzer",
    }
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        clk_freq = int(100e6)
        SoCSDRAM.__init__(self, platform, clk_freq,
            cpu_type=None,
            l2_size=32,
            with_uart=False,
            with_timer=False)

        self.submodules.crg = CRG(platform)
        self.submodules.dna = dna.DNA()
        self.submodules.xadc = xadc.XADC()

        # sdram
        self.submodules.ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"))
        sdram_module = MT41K256M16(self.clk_freq, "1:4")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings)

        # uart
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, period_ns(100e6))


def main():
    parser = argparse.ArgumentParser(description="Nexys LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    platform = nexys_video.Platform()
    soc = BaseSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()
