from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart.bridge import UARTWishboneBridge

from litedram.modules import MT41K128M16
from litedram.phy import a7ddrphy
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

from litescope import LiteScopeAnalyzer

from gateware.info import dna, xadc


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()
        self.clock_domains.cd_clk50 = ClockDomain()

        clk100 = platform.request("clk100")
        rst = platform.request("cpu_reset")

        pll_locked = Signal()
        pll_fb = Signal()
        self.pll_sys = Signal()
        pll_sys4x = Signal()
        pll_sys4x_dqs = Signal()
        pll_clk200 = Signal()
        pll_clk50 = Signal()
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

                     # 50MHz
                     p_CLKOUT4_DIVIDE=32, p_CLKOUT4_PHASE=0.0,
                     o_CLKOUT4=pll_clk50
            ),
            Instance("BUFG", i_I=self.pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_sys4x, o_O=self.cd_sys4x.clk),
            Instance("BUFG", i_I=pll_sys4x_dqs, o_O=self.cd_sys4x_dqs.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            Instance("BUFG", i_I=pll_clk50, o_O=self.cd_clk50.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked | ~rst),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked | rst),
            AsyncResetSynchronizer(self.cd_clk50, ~pll_locked | ~rst),
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


class BaseSoC(SoCSDRAM):
    default_platform = "arty"

    csr_map = {
        "ddrphy":    17,
        "dna":       18,
        "xadc":      19,
        "generator": 20,
        "checker":   21,
        "analyzer":  22
    }
    csr_map.update(SoCSDRAM.csr_map)

    def __init__(self, platform,
                 with_sdram_bist=True, bist_async=True, bist_random=False):
        clk_freq = 100*1000000
        SoCSDRAM.__init__(self, platform, clk_freq,
            cpu_type=None,
            l2_size=32,
            csr_data_width=32,
            with_uart=False,
            with_timer=False)

        self.submodules.crg = _CRG(platform)
        self.submodules.dna = dna.DNA()
        self.submodules.xadc = xadc.XADC()

        # sdram
        self.submodules.ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"))
        sdram_module = MT41K128M16(self.clk_freq, "1:4")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings)

        # sdram bist
        if with_sdram_bist:
            generator_user_port = self.sdram.crossbar.get_port(
                clock_domain="clk50" if bist_async else "sys",
            )
            self.submodules.generator = LiteDRAMBISTGenerator(generator_user_port, random=bist_random)

            checker_user_port = self.sdram.crossbar.get_port(
                clock_domain="clk50" if bist_async else "sys",
            )
            self.submodules.checker = LiteDRAMBISTChecker(checker_user_port, random=bist_random)

        # uart
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # logic analyzer
        analyzer_signals = [Signal(2)]
        if False:
            analyzer_signals = [
                generator_user_port.cmd.valid,
                generator_user_port.cmd.ready,
                generator_user_port.cmd.we,
                generator_user_port.cmd.adr,

                generator_user_port.wdata.valid,
                generator_user_port.wdata.ready,
                generator_user_port.wdata.we,

                self.generator.start.re,
                self.checker.start.re
            ]

        if False:
            gen_data = Signal(32)
            read_data = Signal(32)
            self.comb += [
                gen_data.eq(self.checker.core.gen.o),
                read_data.eq(checker_user_port.rdata.data)
            ]
            analyzer_signals = [
                checker_user_port.cmd.valid,
                checker_user_port.cmd.ready,
                checker_user_port.cmd.we,
                checker_user_port.cmd.adr,

                checker_user_port.rdata.valid,
                checker_user_port.rdata.ready,

                self.generator.start.re,
                self.checker.start.re,

                gen_data,
                read_data,

                self.checker.core.errors
            ]

        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 512)

    def do_exit(self, vns):
        self.analyzer.export_csv(vns, "test/analyzer.csv")


SoC = BaseSoC
