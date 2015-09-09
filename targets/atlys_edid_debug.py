from targets.atlys_hdmi2usb import *

from misoclib.com.uart.phy import UARTPHY
from misoclib.com import uart
from misoclib.tools.wishbone import WishboneStreamingBridge

from litescope.common import *
from litescope.core.port import LiteScopeTerm
from litescope.frontend.la import LiteScopeLA

class UARTVirtualPhy:
    def __init__(self):
        self.sink = Sink([("data", 8)])
        self.source = Source([("data", 8)])


class EDIDDebugSoC(VideomixerSoC):
    csr_map = {
        "la": 30
    }
    csr_map.update(VideomixerSoC.csr_map)

    def __init__(self, platform, with_uart=False, **kwargs):
        VideomixerSoC.__init__(self, platform, with_uart=with_uart, **kwargs)

        uart_sel = platform.request("user_dip", 0)
        self.comb += platform.request("user_led", 0).eq(uart_sel)

        self.submodules.uart_phy = UARTPHY(platform.request("serial"), self.clk_freq, 115200)
        uart_phys = {
            "cpu": UARTVirtualPhy(),
            "bridge": UARTVirtualPhy()
        }
        self.comb += [
            If(uart_sel,
                Record.connect(self.uart_phy.source, uart_phys["bridge"].source),
                Record.connect(uart_phys["bridge"].sink, self.uart_phy.sink),
                uart_phys["cpu"].source.ack.eq(1) # avoid stalling cpu
            ).Else(
                Record.connect(self.uart_phy.source, uart_phys["cpu"].source),
                Record.connect(uart_phys["cpu"].sink, self.uart_phy.sink),
                uart_phys["bridge"].source.ack.eq(1) # avoid stalling bridge
            )
        ]

        # UART cpu
        self.submodules.uart = uart.UART(uart_phys["cpu"])

        # UART bridge
        self.submodules.bridge = WishboneStreamingBridge(uart_phys["bridge"], self.clk_freq)
        self.add_wb_master(self.bridge.wishbone)

        # LiteScope on EDID lines and fsm
        self.hdmi_in0_edid_fsm_state = Signal(4)
        self.debug = (
            self.hdmi_in0.edid.scl,
            self.hdmi_in0.edid.sda_i,
            self.hdmi_in0.edid.sda_o,
            self.hdmi_in0.edid.sda_oe,
            self.hdmi_in0.edid.counter,
            self.hdmi_in0.edid.din,
            self.hdmi_in0_edid_fsm_state
        )
        self.submodules.la = LiteScopeLA(self.debug, 32*1024, with_subsampler=True)
        self.la.trigger.add_port(LiteScopeTerm(self.la.dw))

    def do_finalize(self):
        VideomixerSoC.do_finalize(self)
        self.comb += [
            self.hdmi_in0_edid_fsm_state.eq(self.hdmi_in0.edid.fsm.state)
        ]

    def do_exit(self, vns):
        self.la.export(vns, "../../test/edid_debug/la.csv") # XXX

default_subtarget = EDIDDebugSoC
