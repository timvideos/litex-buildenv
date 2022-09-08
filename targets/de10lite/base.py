import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms import de10lite

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import IS42S16320
from litedram.phy import GENSDRPHY

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_vga    = ClockDomain(reset_less=True)

        # # #

        # Clk / Rst
        clk50 = platform.request("clk50")
        platform.add_period_constraint(clk50, 1e9/50e6)

        # PLL
        pll_locked  = Signal()
        pll_clk_out = Signal(6)
        self.specials += \
            Instance("ALTPLL",
                p_BANDWIDTH_TYPE         = "AUTO",
                p_CLK0_DIVIDE_BY         = 1,
                p_CLK0_DUTY_CYCLE        = 50,
                p_CLK0_MULTIPLY_BY       = 1,
                p_CLK0_PHASE_SHIFT       = "0",
                p_CLK1_DIVIDE_BY         = 1,
                p_CLK1_DUTY_CYCLE        = 50,
                p_CLK1_MULTIPLY_BY       = 1,
                p_CLK1_PHASE_SHIFT       = "-10000",
                p_CLK2_DIVIDE_BY         = 2,
                p_CLK2_DUTY_CYCLE        = 50,
                p_CLK2_MULTIPLY_BY       = 1,
                p_CLK2_PHASE_SHIFT       = "0",
                p_COMPENSATE_CLOCK       = "CLK0",
                p_INCLK0_INPUT_FREQUENCY = 20000,
                p_OPERATION_MODE         = "NORMAL",
                i_INCLK                  = clk50,
                o_CLK                    = pll_clk_out,
                i_CLKENA                 = 0x3f,
                i_EXTCLKENA              = 0xf,
                i_FBIN                   = 1,
                i_PFDENA                 = 1,
                i_PLLENA                 = 1,
                o_LOCKED                 = pll_locked,
            )
        self.comb += [
            self.cd_sys.clk.eq(pll_clk_out[0]),
            self.cd_sys_ps.clk.eq(pll_clk_out[1]),
            self.cd_vga.clk.eq(pll_clk_out[2])
        ]
        self.specials += [
            AsyncResetSynchronizer(self.cd_sys,    ~pll_locked),
            AsyncResetSynchronizer(self.cd_sys_ps, ~pll_locked),
            AsyncResetSynchronizer(self.cd_vga,    ~pll_locked)
        ]

        # SDRAM clock
        self.comb += platform.request("sdram_clock").eq(self.cd_sys_ps.clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
    def __init__(self, sys_clk_freq=int(50e6), **kwargs):
        assert sys_clk_freq == int(50e6)
        platform = de10lite.Platform()

        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform)

        # SDR SDRAM --------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
            sdram_module = IS42S16320(self.clk_freq, "1:1")
            self.register_sdram(self.sdrphy,
                geom_settings   = sdram_module.geom_settings,
                timing_settings = sdram_module.timing_settings)


SoC = BaseSoC
