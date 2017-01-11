"""
Module for info embedded in the gateware / board.
"""

from litex.build.generic_platform import ConstraintError
from litex.gen import *
from litex.soc.interconnect.csr import *

from gateware import i2c
from gateware.info import git
from gateware.info import dna
from gateware.info import platform as platform_info


class Info(Module, AutoCSR):
    def __init__(self, platform, platform_name, target_name):
        self.submodules.dna = dna.DNA()
        self.submodules.git = git.GitInfo()
        self.submodules.platform = platform_info.PlatformInfo(platform_name, target_name)

        try:
            self.submodules.opsis_eeprom = i2c.I2C(platform.request("opsis_eeprom"))
        except ConstraintError:
            pass
