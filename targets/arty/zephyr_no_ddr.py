# Support for the Digilent Arty Board
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import wishbone

from gateware import cas
from gateware import info
from gateware import led
from gateware import spi_flash

from targets.utils import csr_map_update, period_ns


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()
        self.clock_domains.cd_clk100 = ClockDomain()
        self.clock_domains.cd_clk50 = ClockDomain()

        clk100 = platform.request("clk100")
        rst = ~platform.request("cpu_reset")

        clk100bg = Signal()
        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_sys4x = Signal()
        pll_sys4x_dqs = Signal()
        pll_clk200 = Signal()
        pll_clk100 = Signal()
        pll_clk50 = Signal()
        self.specials += [
            Instance("PLLE2_ADV",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1600 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=16, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk100bg, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 50 MHz
                     p_CLKOUT0_DIVIDE=32, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=self.pll_sys,

            ),
            Instance("BUFG", i_I=clk100, o_O=clk100bg),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | rst),
        ]


class BaseSoC(SoCSDRAM):
    csr_peripherals = (
        "spiflash",
        "info",
        "cas",
    )
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    SoCSDRAM.mem_map = {
        "rom":      0x00000000,
        "sram":     0x10000000,
        "main_ram": 0x40000000,
        "csr":      0xe0000000,
    }

    mem_map = {
        "spiflash": 0x20000000,
        "emulator_ram": 0x50000000,
    }
    mem_map.update(SoCSDRAM.mem_map)

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size']=0x8000
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size']=0x8000
        if 'integrated_main_ram_size' not in kwargs:
            kwargs['integrated_main_ram_size']=0x20000;


        clk_freq = int(50e6)
        SoCSDRAM.__init__(self, platform, clk_freq, **kwargs)

        self.submodules.crg = _CRG(platform)
        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, period_ns(clk_freq))

        if self.cpu_type == "vexriscv" and self.cpu_variant == "linux":
            size = 0x4000
            self.submodules.emulator_ram = wishbone.SRAM(size)
            self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, size)

        bios_size = 0x8000
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        self.add_constant("FLASH_BOOT_ADDRESS", self.flash_boot_address)


SoC = BaseSoC
