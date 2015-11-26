#!/usr/bin/env python3

from arty_base import *

from liteeth.common import convert_ip
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone

from litex.gen.fhdl.specials import Keep


class EtherboneSoC(BaseSoC):
    csr_map = {
        "ethphy":  30,
        "ethcore": 31,
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self,
                 mac_address=0x10e2d5000000,
                 ip_address="192.168.1.42",
                 **kwargs):
        platform = arty.Platform()
        BaseSoC.__init__(self, cpu_type=None,
                         integrated_rom_size=0,
                         integrated_main_ram_size=0,
                         csr_data_width=32,
                         **kwargs)

        # Ethernet PHY and UDP/IP stack
        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"),
                                               platform.request("eth"))
        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy,
                                                   mac_address,
                                                   convert_ip(ip_address),
                                                   self.clk_freq,
                                                   with_icmp=True)

        # Etherbone bridge
        self.add_cpu_or_bridge(LiteEthEtherbone(self.ethcore.udp, 20000))
        self.add_wb_master(self.cpu_or_bridge.master.bus)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
create_clock -name sys_clk -period 10 [get_nets sys_clk]
create_clock -name eth_rx_clk -period 40 [get_nets {eth_rx_clk}]
create_clock -name eth_tx_clk -period 40 [get_nets {eth_tx_clk}]

set_false_path -from [get_clocks eth_rx_clk] -to [get_clocks sys_clk]
set_false_path -from [get_clocks sys_clk] -to [get_clocks eth_rx_clk]
set_false_path -from [get_clocks eth_tx_clk] -to [get_clocks sys_clk]
set_false_path -from [get_clocks sys_clk] -to [get_clocks eth_tx_clk]
""", eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)


def main():
    parser = argparse.ArgumentParser(description="LiteX SoC port to Arty")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--build", action="store_true",
                        help="build bitstream")   
    parser.add_argument("--load", action="store_true",
                        help="load bitstream")   
    args = parser.parse_args()

    soc = EtherboneSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, **builder_argdict(args))

    if args.build:
        builder.build()

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.output_dir, "gateware", "top.bit"))


if __name__ == "__main__":
    main()

