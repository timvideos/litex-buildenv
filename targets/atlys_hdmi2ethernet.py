from targets.atlys_base import *

from misoclib.video import dvisampler
from misoclib.video import framebuffer

from misoclib.com.liteeth.common import *
from misoclib.com.liteeth.phy import LiteEthPHY
from misoclib.com.liteeth.phy.mii import LiteEthPHYMII
from misoclib.com.liteeth.core import LiteEthUDPIPCore
from misoclib.com.liteeth.frontend.etherbone import LiteEthEtherbone

from hdl.encoder import EncoderReader, Encoder
from hdl.stream import UDPStreamer

class EtherboneSoC(BaseSoC):
    csr_map = {
        "ethphy": 17,
        "ethcore": 18,
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self, platform,
        mac_address=0x10e2d5000000,
        ip_address="192.168.1.42",
        **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        # Ethernet PHY and UDP/IP stack
        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"), platform.request("eth"))
        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy, mac_address, convert_ip(ip_address), self.clk_freq, with_icmp=False)

        # Etherbone bridge
        self.submodules.etherbone = LiteEthEtherbone(self.ethcore.udp, 20000)
        self.add_wb_master(self.etherbone.master.bus)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_clocks_rx}" TNM_NET = "GRPeth_clocks_rx";
NET "{eth_rx_clk}" TNM_NET = "GRPeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "GRPeth_tx_clk";
TIMESPEC "TSise_sucks1" = FROM "GRPeth_clocks_rx" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks2" = FROM "GRPsys_clk" TO "GRPeth_clocks_rx" TIG;
TIMESPEC "TSise_sucks3" = FROM "GRPeth_tx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks4" = FROM "GRPsys_clk" TO "GRPeth_tx_clk" TIG;
TIMESPEC "TSise_sucks5" = FROM "GRPeth_rx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks6" = FROM "GRPsys_clk" TO "GRPeth_rx_clk" TIG;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)


class VideomixerSoC(EtherboneSoC):
    csr_map = {
        "fb":                  19,
        "dvisampler":          20,
        "dvisampler_edid_mem": 21
    }
    csr_map.update(EtherboneSoC.csr_map)

    interrupt_map = {
        "dvisampler": 3,
    }
    interrupt_map.update(EtherboneSoC.interrupt_map)

    def __init__(self, platform, **kwargs):
        EtherboneSoC.__init__(self, platform, **kwargs)
        self.submodules.dvisampler = dvisampler.DVISampler(platform.request("dvi_in", 1),
                                                           self.sdram.crossbar.get_master(),
                                                           fifo_depth=4096)
        self.submodules.fb = framebuffer.Framebuffer(None, platform.request("dvi_out"),
                                                     self.sdram.crossbar.get_master())
        platform.add_platform_command("""PIN "dviout_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command("""
NET "{pix_clk}" TNM_NET = "GRPpix_clk";
TIMESPEC "TSise_sucks7" = FROM "GRPpix_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks8" = FROM "GRPsys_clk" TO "GRPpix_clk" TIG;
""", pix_clk=self.fb.driver.clocking.cd_pix.clk)


class HDMI2EthernetSoC(VideomixerSoC):
    csr_map = {
        "encoder_reader": 22
    }
    csr_map.update(VideomixerSoC.csr_map)
    mem_map = {
        "encoder": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(VideomixerSoC.mem_map)

    def __init__(self, platform, **kwargs):
        VideomixerSoC.__init__(self, platform, **kwargs)

        self.submodules.encoder_reader = EncoderReader(self.sdram.crossbar.get_master())
        self.submodules.encoder = Encoder(platform)
        encoder_port = self.ethcore.udp.crossbar.get_port(8000, 8)
        self.submodules.encoder_streamer = UDPStreamer(convert_ip("192.168.1.15"), 8000)

        self.comb += [
            platform.request("user_led", 0).eq(self.encoder_reader.source.stb),
            platform.request("user_led", 1).eq(self.encoder_reader.source.ack),
            Record.connect(self.encoder_reader.source, self.encoder.sink),
            Record.connect(self.encoder.source, self.encoder_streamer.sink),
            Record.connect(self.encoder_streamer.source, encoder_port.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"]+self.shadow_base, 0x2000)


default_subtarget = HDMI2EthernetSoC
