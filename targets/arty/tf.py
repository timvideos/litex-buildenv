# Support for the Digilent Arty Board
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import Pins, Subsignal, IOStandard, Misc
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import wishbone
from litex.soc.cores.bitbang import I2CMaster

from litedram.modules import MT41K128M16
from litedram.phy import a7ddrphy
from litedram.core import ControllerSettings

from gateware import cas
from gateware import info
from gateware import led
from gateware import spi_flash

from targets.utils import csr_map_update, period_ns
from targets.arty.base import BaseSoC

i2c_pmod_d =  [
    ("i2c_pmodd", 0,
        Subsignal("scl", Pins("F3"), Misc("PULLUP")),
        Subsignal("sda", Pins("D3"), Misc("PULLUP")),
        Subsignal("scl_pup", Pins("A14")),
        Subsignal("sda_pup", Pins("A13")),
        IOStandard("LVCMOS33"),
    ),
]

class TFSoC(BaseSoC):

    def __init__(self, platform, spiflash="spiflash_1x", **kwargs):
        BaseSoC.__init__(self, platform, spiflash, **kwargs)
        platform.add_extension(i2c_pmod_d)
        # i2c master
        i2c_pads = platform.request("i2c_pmodd", 0)
        self.submodules.i2c0 = I2CMaster(i2c_pads)
        self.add_csr("i2c0")


SoC = TFSoC
