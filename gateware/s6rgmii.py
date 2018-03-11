# RGMII PHY for Spartan-6
from liteeth.common import *

from migen.genlib.io import DDROutput
from migen.genlib.misc import WaitTimer
from migen.genlib.fsm import FSM, NextState

from migen.genlib.resetsync import AsyncResetSynchronizer

from liteeth.phy.common import *

class LiteEthPHYRGMIICRG(Module, AutoCSR):
    def __init__(self, clock_pads, pads):
        self.reset = CSRStorage()

        # # #

        reset = self.reset.storage

        self.clock_domains.cd_eth_rx = ClockDomain()
        self.clock_domains.cd_eth_tx = ClockDomain()

        self.comb += self.cd_eth_tx.clk.eq(self.cd_eth_rx.clk)

        self.comb += pads.rst_n.eq(~reset)
        self.specials += [
            AsyncResetSynchronizer(self.cd_eth_tx, reset),
            AsyncResetSynchronizer(self.cd_eth_rx, reset)
        ]


class LiteEthPHYRGMII(Module, AutoCSR):
    def __init__(self, clock_pads, pads):
        self.dw = 8
        self.submodules.crg = LiteEthPHYRGMIICRG(clock_pads, pads)
        self.sink = stream.Endpoint(eth_phy_description(8))
        self.source = stream.Endpoint(eth_phy_description(8))

        rx_dv = Signal()
        rxd = Signal(8)

        tx_data = Signal(8)
        tx_valid = Signal()
        self.sync.eth_tx += [
            tx_data.eq(self.sink.data),
            tx_valid.eq(self.sink.valid)
        ]

        self.specials += Instance("rgmii_if",
            i_tx_reset=self.crg.reset.storage,
            i_rx_reset=self.crg.reset.storage,

            o_rgmii_txd=pads.tx_data,
            o_rgmii_tx_ctl=pads.tx_ctl,
            o_rgmii_txc=clock_pads.tx,

            i_rgmii_rxd=pads.rx_data,
            i_rgmii_rx_ctl=pads.rx_ctl,
            i_rgmii_rxc=clock_pads.rx,

            #o_link_status=,
            #o_clock_speed=,
            #o_duplex_status=,

            i_txd_from_mac=tx_data,
            i_tx_en_from_mac=tx_valid,
            i_tx_er_from_mac=0,
            i_tx_clk=self.crg.cd_eth_tx.clk,

            #o_crs_to_mac=,
            #o_col_to_mac=,

            o_rxd_to_mac=rxd,
            o_rx_dv_to_mac=rx_dv,
            #o_rx_er_to_mac=,
            o_rx_clk=self.crg.cd_eth_rx.clk
        )

        self.comb += self.sink.ready.eq(1)

        rx_dv_d = Signal()
        self.sync.eth_rx += rx_dv_d.eq(rx_dv)

        last = Signal()
        self.sync.eth_rx += [
            self.source.valid.eq(rx_dv),
            self.source.data.eq(rxd)
        ]
        self.comb += self.source.last.eq(~rx_dv & rx_dv_d)

        if hasattr(pads, "mdc"):
            self.submodules.mdio = LiteEthPHYMDIO(pads)
