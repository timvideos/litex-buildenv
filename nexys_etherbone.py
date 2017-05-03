#!/usr/bin/env python3

from nexys_base import *

from litex.soc.cores.uart import UARTWishboneBridge

from liteeth.common import convert_ip
from liteeth.phy.s7rgmii import LiteEthPHYRGMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk200 = ClockDomain()
        self.clock_domains.cd_clk100 = ClockDomain()

        clk100 = platform.request("clk100")
        rst = platform.request("cpu_reset")

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1400 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=14, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk100, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 140 MHz
                     p_CLKOUT0_DIVIDE=10, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

                     # 200 MHz
                     p_CLKOUT1_DIVIDE=7, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_clk200,
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            Instance("BUFG", i_I=clk100, o_O=self.cd_clk100.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk100, ~pll_locked | ~rst),
        ]

        reset_counter = Signal(4, reset=15)
        ic_reset = Signal(reset=1)
        self.sync.clk200 += \
            If(reset_counter != 0,
                reset_counter.eq(reset_counter - 1)
            ).Else(
                ic_reset.eq(0)
            )
        self.specials += Instance("IDELAYCTRL", i_REFCLK=ClockSignal("clk200"), i_RST=ic_reset)


class BaseSoC(SoCSDRAM):
    csr_map = {
        "dna":    18,
        "xadc":   19,
        "oled":   20
    }
    csr_map.update(SoCSDRAM.csr_map)

    def __init__(self, platform, **kwargs):
        clk_freq = 142*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            integrated_main_ram_size=0x8000,
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            **kwargs)

        self.submodules.crg = _CRG(platform)


class EtherboneSoC(BaseSoC):
    csr_map = {
        "ethphy":  30,
        "ethcore": 31,
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self,
                 platform,
                 mac_address=0x10e2d5000000,
                 ip_address="192.168.1.50"):
        BaseSoC.__init__(self, platform, cpu_type=None, csr_data_width=32, with_uart=False)

        # uart
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), self.clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)


#        # Ethernet PHY and UDP/IP stack
#        self.submodules.ethphy = LiteEthPHYRGMII(self.platform.request("eth_clocks"),
#                                                 self.platform.request("eth"))
#        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy,
#                                                   mac_address,
#                                                   convert_ip(ip_address),
#                                                   self.clk_freq,
#                                                   with_icmp=True)
#
#        # Etherbone bridge
#        self.submodules.etherbone = LiteEthEtherbone(self.ethcore.udp, 20000)
#        self.add_wb_master(self.etherbone.wishbone.bus)
#
#
#        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
#        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
#        self.platform.add_period_constraint(self.crg.cd_sys.clk, 10.0)
#        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 8.0)
#        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 8.0)
#
#        self.platform.add_false_path_constraints(
#            self.crg.cd_sys.clk,
#            self.ethphy.crg.cd_eth_rx.clk,
#            self.ethphy.crg.cd_eth_tx.clk)

def main():
    parser = argparse.ArgumentParser(description="Nexys LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = nexys.Platform()
    soc = EtherboneSoC(platform)
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()

