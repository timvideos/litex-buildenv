# Support for the Digilent Cmod A7 Board

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer


class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk200 = ClockDomain()
        clk12 = platform.request("clk12")
        rst = platform.request("user_btn", 0)
        self.specials += [
            Instance("BUFG", i_I=clk12, o_O=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys, rst),
        ]
