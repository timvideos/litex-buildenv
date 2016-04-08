from migen.fhdl.specials import Keep
from migen.flow.actor import *
from migen.actorlib.fifo import AsyncFIFO, SyncFIFO

from misoclib.soc import mem_decoder

from liteeth.common import *
from liteeth.phy import LiteEthPHY
from liteeth.phy.mii import LiteEthPHYMII
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone

from gateware.hdmi_in import HDMIIn
from gateware.hdmi_out import HDMIOut
from gateware.encoder import Encoder
from gateware.encoder.dma import EncoderDMAReader
from gateware.encoder.buffer import EncoderBuffer
from gateware.streamer import UDPStreamer

from targets.common import *
from targets.atlys_base import BaseSoC
from targets.atlys_video import CreateVideoMixerSoC

class EtherboneSoC(BaseSoC):
    csr_peripherals = (
        "ethphy",
        "ethcore"
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(
            self,
            platform,
            mac_address=0x10e2d5000000,
            ip_address="192.168.1.42",
            **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        # Ethernet PHY and UDP/IP stack
        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"), platform.request("eth"))
        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy, mac_address, convert_ip(ip_address), int(self.clk_freq), with_icmp=False)

        # Etherbone bridge
        self.submodules.etherbone = LiteEthEtherbone(self.ethcore.udp, 20000)
        self.add_wb_master(self.etherbone.master.bus)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
# Separate TMNs for FROM:TO TIG constraints
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_clocks_rx}" TNM_NET = "TIGeth_clocks_rx";
TIMESPEC "TSeth_clocks_rx_to_sys" = FROM "TIGeth_clocks_rx" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_clocks_rx" = FROM "TIGsys_clk" TO "TIGeth_clocks_rx" TIG;

NET "{eth_clocks_tx}" TNM_NET = "TIGeth_clocks_tx";
TIMESPEC "TSeth_clocks_tx_to_sys" = FROM "TIGeth_clocks_tx" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_clocks_tx" = FROM "TIGsys_clk" TO "TIGeth_clocks_tx" TIG;

NET "{eth_rx_clk}" TNM_NET = "TIGeth_rx_clk";
TIMESPEC "TSeth_rx_to_sys" = FROM "TIGeth_rx_clk" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_rx" = FROM "TIGsys_clk" TO "TIGeth_rx_clk" TIG;

NET "{eth_tx_clk}" TNM_NET = "TIGeth_tx_clk";
TIMESPEC "TSeth_tx_to_sys" = FROM "TIGeth_tx_clk" TO "TIGsys_clk" TIG;
TIMESPEC "TSsys_to_eth_tx" = FROM "TIGsys_clk" TO "TIGeth_tx_clk" TIG;
""",
            eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
            eth_clocks_tx=platform.lookup_request("eth_clocks").tx,
            eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
            eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk,
        )


EtherVideoMixerSoC = CreateVideoMixerSoC(EtherboneSoC)


class HDMI2EthSoC(EtherVideoMixerSoC):
    csr_peripherals = (
        "encoder_reader",
        "encoder",
    )
    csr_map_update(EtherVideoMixerSoC.csr_map, csr_peripherals)
    mem_map = {
        "encoder": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(EtherVideoMixerSoC.mem_map)

    def __init__(self, platform, **kwargs):
        EtherVideoMixerSoC.__init__(self, platform, **kwargs)

        lasmim = self.sdram.crossbar.get_master()
        self.submodules.encoder_reader = EncoderDMAReader(lasmim)
        self.submodules.encoder_cdc = RenameClockDomains(AsyncFIFO([("data", 128)], 4),
                                          {"write": "sys", "read": "encoder"})
        self.submodules.encoder_buffer = RenameClockDomains(EncoderBuffer(), "encoder")
        self.submodules.encoder_fifo = RenameClockDomains(SyncFIFO(EndpointDescription([("data", 16)], packetized=True), 16), "encoder")
        self.submodules.encoder = Encoder(platform)
        encoder_port = self.ethcore.udp.crossbar.get_port(8000, 8)
        self.submodules.encoder_streamer = UDPStreamer(convert_ip("192.168.1.15"), 8000)

        self.comb += [
            platform.request("user_led", 0).eq(self.encoder_reader.source.stb),
            platform.request("user_led", 1).eq(self.encoder_reader.source.ack),
            Record.connect(self.encoder_reader.source, self.encoder_cdc.sink),
            Record.connect(self.encoder_cdc.source, self.encoder_buffer.sink),
            Record.connect(self.encoder_buffer.source, self.encoder_fifo.sink),
            Record.connect(self.encoder_fifo.source, self.encoder.sink),
            Record.connect(self.encoder.source, self.encoder_streamer.sink),
            Record.connect(self.encoder_streamer.source, encoder_port.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"]+self.shadow_base, 0x2000)


default_subtarget = HDMI2EthSoC
