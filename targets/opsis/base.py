# Support for Numato Opsis - https://opsis.hdmi2usb.tv

from migen import *
from migen.genlib.misc import WaitTimer

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.interconnect.csr import AutoCSR
from litex.soc.interconnect import wishbone

from litedram.modules import MT41J128M16
from litedram.phy import s6ddrphy
from litedram.core import ControllerSettings

#from gateware import cas
from gateware import i2c
from gateware import info
from gateware import opsis_i2c
from gateware import shared_uart
from gateware import tofe
from gateware import spi_flash

from .crg import _CRG

from targets.utils import dict_set_max, define_flash_constants


class FrontPanelGPIO(Module, AutoCSR):
    def __init__(self, platform, clk_freq):
        switches = Signal(1)
        leds = Signal(2)

        self.reset = Signal()

        # # #

        self.submodules.switches = GPIOIn(switches)
        self.submodules.leds = GPIOOut(leds)
        self.comb += [
           switches[0].eq(~platform.request("pwrsw")),
           platform.request("hdled").eq(~leds[0]),
           platform.request("pwled").eq(~leds[1]),
        ]

        # generate a reset when power switch is pressed for 1 second
        self.submodules.reset_timer = WaitTimer(clk_freq)
        self.comb += [
            self.reset_timer.wait.eq(switches[0]),
            self.reset.eq(self.reset_timer.done)
        ]


class BaseSoC(SoCSDRAM):
    mem_map = {**SoCSDRAM.mem_map, **{
        'spiflash': 0x20000000,
    }}

    def __init__(self, platform, **kwargs):
        if kwargs.get('cpu_type', None) == "mor1kx":
            dict_set_max(kwargs, 'integrated_rom_size', 0x10000)
        else:
            dict_set_max(kwargs, 'integrated_rom_size', 0x8000)
        dict_set_max(kwargs, 'integrated_sram_size', 0x8000)

        sys_clk_freq = 50*1000000

        if 'expansion' in kwargs:
            tofe_board_name = kwargs.get('expansion')
            del kwargs['expansion']
        else:
            tofe_board_name = None

        # disable uart
        kwargs['with_uart'] = False

        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/sys_clk_freq)

        # Add specialized uart ---------------------------------------------------------------------
        self.submodules.suart = shared_uart.SharedUART(self.clk_freq, 115200)
        self.suart.add_uart_pads(platform.request('fx2_serial'))
        self.submodules.uart = self.suart.uart
        self.add_csr("uart")
        self.add_interrupt("uart")

        # DDR3 SDRAM -------------------------------------------------------------------------------
        if True:
            sdram_module = MT41J128M16(sys_clk_freq, "1:4")
            self.submodules.ddrphy = s6ddrphy.S6QuarterRateDDRPHY(
                platform.request("ddram"),
                rd_bitslip   = 0,
                wr_bitslip   = 4,
                dqs_ddr_alignment="C0")
            self.add_csr("ddrphy")
            controller_settings = ControllerSettings(
                with_bandwidth=True)
            self.register_sdram(
                self.ddrphy,
                geom_settings   = sdram_module.geom_settings,
                timing_settings = sdram_module.timing_settings,
                controller_settings=controller_settings)
            self.comb += [
                self.ddrphy.clk8x_wr_strb.eq(self.crg.clk8x_wr_strb),
                self.ddrphy.clk8x_rd_strb.eq(self.crg.clk8x_rd_strb),
            ]

        # Basic peripherals ------------------------------------------------------------------------
        # info module
        self.submodules.info = info.Info(platform, self.__class__.__name__)
        self.add_csr("info")
        # control and status module
        #self.submodules.cas = cas.ControlAndStatus(platform, sys_clk_freq)
        self.add_csr("cas")
        # opsis specific i2c module
        self.submodules.opsis_i2c = opsis_i2c.OpsisI2C(platform)
        self.add_csr("opsis_i2c")
        # front panel (ATX) module
        self.submodules.front_panel = FrontPanelGPIO(platform, sys_clk_freq)
        self.comb += self.crg.reset.eq(self.front_panel.reset)
        self.add_csr("front_panel")

        # Expansion boards -------------------------------------------------------------------------
        if tofe_board_name:
            if tofe_board_name == 'lowspeedio':
                self.submodules.tofe = tofe.TOFEBoard(tofe_board_name)(platform, self.suart)
            else:
                self.submodules.tofe = tofe.TOFEBoard(tofe_board_name)(platform)

        # Add debug interface if the CPU has one ---------------------------------------------------
        if hasattr(self.cpu, "debug_bus"):
            self.register_mem(
                name="vexriscv_debug",
                address=0xf00f0000,
                interface=self.cpu.debug_bus,
                size=0x100)

        # Memory mapped SPI Flash ------------------------------------------------------------------
        self.submodules.spiflash = spi_flash.SpiFlash(
            platform.request("spiflash4x"),
            dummy=platform.spiflash_read_dummy_bits,
            div=platform.spiflash_clock_div,
            endianness=self.cpu.endianness)
        self.add_csr("spiflash")
        self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        self.add_constant("SPIFLASH_TOTAL_SIZE", platform.spiflash_total_size)
        self.add_wb_slave(
            self.mem_map["spiflash"],
            self.spiflash.bus,
            platform.spiflash_total_size)
        self.add_memory_region(
            "spiflash",
            self.mem_map["spiflash"],
            platform.spiflash_total_size)

        bios_size = 0x8000
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size
        define_flash_constants(self)


SoC = BaseSoC
