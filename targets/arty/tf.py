# Support for the Digilent Arty Board

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.cores.bitbang import I2CMaster

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
