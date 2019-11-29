from migen.fhdl.decorators import ClockDomainsRenamer, ResetInserter
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.interconnect import stream
from litex.soc.cores.uart import UART

from gateware.encoder import EncoderDMAReader, EncoderBuffer, Encoder
from gateware.streamer import USBStreamer
from gateware.fx2_crossbar import FX2Crossbar, FX2PHY

from targets.utils import csr_map_update
from targets.atlys.video import SoC as BaseSoC


class HDMI2USBSoC(BaseSoC):
    csr_peripherals = (
        "encoder_reader",
        "encoder",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)
    mem_map = {
        "encoder": 0x50000000,  # (shadow @0xd0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, with_uart=False, *args, **kwargs)

        encoder_port = self.sdram.crossbar.get_port(
            mode="read",
            data_width=128,
            reverse=True,
        )
        self.submodules.encoder_reader = EncoderDMAReader(encoder_port)
        encoder_cdc = stream.AsyncFIFO([("data", 128)], 4)
        encoder_cdc = ClockDomainsRenamer({"write": "sys",
                                           "read": "encoder"})(encoder_cdc)
        encoder_buffer = ClockDomainsRenamer("encoder")(EncoderBuffer())
        encoder = Encoder(platform)
        xbar = FX2Crossbar(platform)
        self.submodules += encoder_cdc, encoder_buffer, encoder, xbar

        self.comb += [
            self.encoder_reader.source.connect(encoder_cdc.sink),
            encoder_cdc.source.connect(encoder_buffer.sink),
            encoder_buffer.source.connect(encoder.sink),
            encoder.source.connect(xbar.get_in_fifo(0))
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), encoder.bus)
        self.add_memory_region("encoder",
            self.mem_map["encoder"] + self.shadow_base, 0x2000)

        self.crg.cd_encoder.clk.attr.add("keep")

        fx2_uart_sink = xbar.get_in_fifo(1, clock_domain=self.crg.cd_sys)
        fx2_uart_source = xbar.get_out_fifo(0, clock_domain=self.crg.cd_sys)

        self.submodules.uart_phy = uart_phy = FX2PHY(fx2_uart_sink, fx2_uart_source)
        self.submodules.uart = uart = ResetInserter()(UART(uart_phy))

        self.add_csr("uart", allow_user_defined=True)
        self.add_interrupt("uart", allow_user_defined=True)


SoC = HDMI2USBSoC
