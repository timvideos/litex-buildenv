#!/usr/bin/env python3
import argparse
import os

from litex.gen import *
from litex.gen.genlib.resetsync import AsyncResetSynchronizer
from litex.gen.fhdl.specials import Keep

from litex.boards.platforms import arty

from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.cores.flash import spi_flash
from litex.soc.cores.sdram.settings import SDRAMModule
from litex.soc.cores.uart.core import RS232PHY, UART
from litex.soc.integration.builder import *
from litex.soc.interconnect.wishbonebridge import WishboneStreamingBridge

from litex.soc.interconnect.stream import *

from liteeth.phy import LiteEthPHY
from liteeth.core.mac import LiteEthMAC

from gateware import a7ddrphy, firmware
from gateware import dna, xadc, led

# TODO: use half-rate DDR3 phy and use 100Mhz CPU clock

class UARTVirtualPhy:
    def __init__(self):
        self.sink = Endpoint([("data", 8)])
        self.source = Endpoint([("data", 8)])


class MT41K128M16(SDRAMModule):
    memtype = "DDR3"
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings (-7 speedgrade)
    tRP   = 13.75
    tRCD  = 13.75
    tWR   = 15
    tWTR  = 8
    tREFI = 64*1000*1000/8192
    tRFC  = 160


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()

        clk100 = platform.request("clk100")
        rst = platform.request("cpu_reset")

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_sys4x = Signal()
        pll_sys4x_dqs = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1600 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=16, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk100, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 100 MHz
                     p_CLKOUT0_DIVIDE=16, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

                     # 400 MHz
                     p_CLKOUT1_DIVIDE=4, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_sys4x,

                     # 400 MHz dqs
                     p_CLKOUT2_DIVIDE=4, p_CLKOUT2_PHASE=90.0,
                     o_CLKOUT2=pll_sys4x_dqs,

                     # 200 MHz
                     p_CLKOUT3_DIVIDE=8, p_CLKOUT3_PHASE=0.0,
                     o_CLKOUT3=pll_clk200,

                     # 400MHz
                     p_CLKOUT4_DIVIDE=4, p_CLKOUT4_PHASE=0.0,
                     #o_CLKOUT4=
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_sys4x, o_O=self.cd_sys4x.clk),
            Instance("BUFG", i_I=pll_sys4x_dqs, o_O=self.cd_sys4x_dqs.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked | rst),
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

        eth_clk = Signal()
        self.specials += [
            Instance("BUFR", p_BUFR_DIVIDE="4", i_CE=1, i_CLR=0, i_I=clk100, o_O=eth_clk),
            Instance("BUFG", i_I=eth_clk, o_O=platform.request("eth_ref_clk")),
        ]

class BaseSoC(SoCSDRAM):
    default_platform = "arty"

    csr_map = {
        "spiflash": 16,
        "ddrphy":   17,
        "dna":      18,
        "xadc":     19,
        "leds":     20,
        "rgb_leds": 21
    }
    csr_map.update(SoCSDRAM.csr_map)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self,
                 platform,
                 firmware_ram_size=0x10000,
                 firmware_filename="firmware/firmware.bin",
                 **kwargs):
        clk_freq = 100*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            integrated_rom_size=0x8000,
            integrated_sram_size=0x8000,
            with_uart=False,
            **kwargs)

        self.submodules.crg = _CRG(platform)
        self.submodules.dna = dna.DNA()
        self.submodules.xadc = xadc.XADC()

        self.submodules.leds = led.ClassicLed(Cat(platform.request("user_led", i) for i in range(4)))
        self.submodules.rgb_leds = led.RGBLed(platform.request("rgb_leds"))

        # firmware
        self.submodules.firmware_ram = firmware.FirmwareROM(firmware_ram_size, firmware_filename)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)
        self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["firmware_ram"])

        # sdram
        self.submodules.ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"))
        sdram_module = MT41K128M16(self.clk_freq, "1:4")
        self.register_sdram(self.ddrphy, "minicon",
                            sdram_module.geom_settings, sdram_module.timing_settings)
        self.add_constant("SDRAM_ISERDESE2_BITSLIP", 2)
        self.add_constant("SDRAM_IDELAYE2_DELAY", 6)

        # spi flash
        if not self.integrated_rom_size:
            spiflash_pads = platform.request("spiflash")
            spiflash_pads.clk = Signal()
            self.specials += Instance("STARTUPE2",
                                      i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0, i_PACK=0,
                                      i_USRCCLKO=spiflash_pads.clk, i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
            self.submodules.spiflash = spi_flash.SpiFlash(spiflash_pads, dummy=11, div=2)
            self.add_constant("SPIFLASH_PAGE_SIZE", 256)
            self.add_constant("SPIFLASH_SECTOR_SIZE", 0x10000)
            self.flash_boot_address = 0xb00000
            self.register_rom(self.spiflash.bus)

        # uart mux
        uart_sel = platform.request("user_sw", 0)

        self.submodules.uart_phy = RS232PHY(platform.request("serial"), self.clk_freq, 115200)
        uart_phys = {
            "cpu": UARTVirtualPhy(),
            "bridge": UARTVirtualPhy()
        }
        self.comb += [
            If(uart_sel,
                self.uart_phy.source.connect(uart_phys["bridge"].source),
                uart_phys["bridge"].sink.connect(self.uart_phy.sink),
                uart_phys["cpu"].source.ready.eq(1) # avoid stalling cpu
            ).Else(
                self.uart_phy.source.connect(uart_phys["cpu"].source),
                uart_phys["cpu"].sink.connect(self.uart_phy.sink),
                uart_phys["bridge"].source.ready.eq(1) # avoid stalling bridge
            )
        ]

        # uart cpu
        self.submodules.uart = UART(uart_phys["cpu"])

        # uart bridge
        self.submodules.bridge = WishboneStreamingBridge(uart_phys["bridge"], self.clk_freq)
        self.add_wb_master(self.bridge.wishbone)


class MiniSoC(BaseSoC):
    csr_map = {
        "ethphy": 30,
        "ethmac": 31
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "ethmac": 2,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, *args, **kwargs):
        BaseSoC.__init__(self, *args, **kwargs)

        self.submodules.ethphy = LiteEthPHY(self.platform.request("eth_clocks"),
                                            self.platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]

        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 40.0)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 40.0)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk,
            self.ethphy.crg.cd_eth_tx.clk)

    def configure_ip(self, ip_type, ip):
        for i, e in enumerate(ip):
            s = ip_type + str(i + 1)
            s = s.upper()
            self.add_constant(s, e)

def main():
    parser = argparse.ArgumentParser(description="Arty LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--with-ethernet", action="store_true",
                        help="enable Ethernet support")
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = arty.Platform()
    cls = MiniSoC if args.with_ethernet else BaseSoC
    soc = cls(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()
