from migen.fhdl.std import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from misoclib.soc import mem_decoder
from misoclib.soc.sdram import SDRAMSoC
from misoclib.mem.flash import spiflash
from misoclib.mem.sdram.module import SDRAMModule
from misoclib.mem.sdram.core.minicon import MiniconSettings

from liteeth.phy import LiteEthPHY
from liteeth.core.mac import LiteEthMAC

from gateware import a7ddrphy, dna, xadc, led

# TODO: use half-rate DDR3 phy and use 100Mhz CPU clock

class MT41K128M16(SDRAMModule):
    geom_settings = {
        "nbanks": 8,
        "nrows":  16384,
        "ncols":  1024,
    }
    timing_settings = {
        "tRP":   13.75,
        "tRCD":  13.75,
        "tWR":   15,
        "tWTR":  8,
        "tREFI": 64*1000*1000/8192,
        "tRFC":  160,
    }

    def __init__(self, clk_freq):
        SDRAMModule.__init__(self, clk_freq, "DDR3", self.geom_settings,
                             self.timing_settings)


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

                     # VCO @ 800 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=8, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk100, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 50 MHz
                     p_CLKOUT0_DIVIDE=16, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

                     # 200 MHz
                     p_CLKOUT1_DIVIDE=4, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_sys4x,

                     # 200 MHz dqs
                     p_CLKOUT2_DIVIDE=4, p_CLKOUT2_PHASE=135.0,
                     o_CLKOUT2=pll_sys4x_dqs,

                     # 200 MHz
                     p_CLKOUT3_DIVIDE=4, p_CLKOUT3_PHASE=0.0,
                     o_CLKOUT3=pll_clk200,

                     # 200MHz
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

class BaseSoC(SDRAMSoC):
    default_platform = "arty"

    csr_map = {
        "spiflash": 16,
        "ddrphy":   17,
        "dna":      18,
        "xadc":     19,
        "leds":     20,
        "rgb_leds": 21
    }
    csr_map.update(SDRAMSoC.csr_map)

    def __init__(self, platform, sdram_controller_settings=MiniconSettings(),
                 integrated_rom_size=0x8000,       # TODO: remove this when SPI Flash validated
                 integrated_main_ram_size=0x8000,  # TODO: remove this when SDRAM validated
                 **kwargs):
        SDRAMSoC.__init__(self, platform,
                          clk_freq=50000000,
                          integrated_rom_size=integrated_rom_size,
                          integrated_main_ram_size=integrated_main_ram_size,
                          sdram_controller_settings=sdram_controller_settings,
                          **kwargs)

        self.submodules.crg = _CRG(platform)
        self.submodules.dna = dna.DNA()
        self.submodules.xadc = xadc.XADC()

        self.submodules.leds = led.ClassicLed(Cat(platform.request("user_led", i) for i in range(4)))
        self.submodules.rgb_leds = led.RGBLed(platform.request("rgb_leds"))

        if not self.integrated_main_ram_size:
            ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"),
                                       MT41K128M16(self.clk_freq))
            self.submodules.ddrphy = ddrphy
            self.register_sdram_phy(ddrphy)

        if not self.integrated_rom_size:
            spiflash_pads = platform.request("spiflash")
            spiflash_pads.clk = Signal()
            self.specials += Instance("STARTUPE2",
                                      i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0,
                                      i_PACK=0, i_USRCCLKO=spiflash_pads.clk,
                                      i_USRCCLKTS=0, i_USRDONEO=1,
                                      i_USRDONETS=1)
            self.submodules.spiflash = spiflash.SpiFlash(spiflash_pads,
                                                         dummy=11, div=2)
            self.add_constant("SPIFLASH_PAGE_SIZE", 256)
            self.add_constant("SPIFLASH_SECTOR_SIZE", 0x10000)
            self.flash_boot_address = 0xb00000
            self.register_rom(self.spiflash.bus)


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

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.ethphy = LiteEthPHY(platform.request("eth_clocks"),
                                            platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
                                            interface="wishbone",
                                            with_preamble_crc=False)
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac",
                               self.mem_map["ethmac"] | self.shadow_base,
                               0x2000)

default_subtarget = MiniSoC
