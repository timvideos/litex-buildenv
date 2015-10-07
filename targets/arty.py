from migen.fhdl.std import *

from misoclib.soc import mem_decoder
from misoclib.soc.sdram import SDRAMSoC
from misoclib.mem.flash import spiflash
from misoclib.mem.sdram.phy import k7ddrphy
from misoclib.mem.sdram.module import MT41K128M16
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.com.liteethmini.phy import LiteEthPHY
from misoclib.com.liteethmini.mac import LiteEthMAC


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)

        clk100 = platform.request("clk100")

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_sys4x = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 800MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=8, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk100, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 100MHz
                     p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

                     # 400MHz
                     p_CLKOUT1_DIVIDE=2, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_sys4x,

                     p_CLKOUT2_DIVIDE=5, p_CLKOUT2_PHASE=0.0, #o_CLKOUT2=,

                     p_CLKOUT3_DIVIDE=2, p_CLKOUT3_PHASE=0.0, #o_CLKOUT3=,

                     p_CLKOUT4_DIVIDE=4, p_CLKOUT4_PHASE=0.0, #o_CLKOUT4=
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_sys4x, o_O=self.cd_sys4x.clk),
        ]


class BaseSoC(SDRAMSoC):
    default_platform = "arty"

    csr_map = {
        "spiflash": 16,
        "ddrphy":   17,
    }
    csr_map.update(SDRAMSoC.csr_map)

    def __init__(self, platform, sdram_controller_settings=LASMIconSettings(),
                 **kwargs):
        SDRAMSoC.__init__(self, platform,
                          clk_freq=int((1/platform.default_clk_period)*1e9),
                          sdram_controller_settings=sdram_controller_settings,
                          **kwargs)

        self.submodules.crg = _CRG(platform)

        if not self.integrated_main_ram_size:
            ddrphy = k7ddrphy.K7DDRPHY(platform.request("ddram"),
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
        "ethphy": 20,
        "ethmac": 21
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

default_subtarget = BaseSoC
