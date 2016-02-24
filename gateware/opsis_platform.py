from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, iMPACT

_io = [
    ("clk100", 0, Pins("AB13"), IOStandard("LVCMOS33")),
    ("cpu_reset", 0, Pins("Y3"), IOStandard("LVCMOS15"), Misc("PULLUP")),
    ("serial", 0,
        Subsignal("tx", Pins("A19")),
        Subsignal("rx", Pins("C19")),
        IOStandard("LVCMOS33")),
]


class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.0

    def __init__(self):
        XilinxPlatform.__init__(self,  "xc6slx45t-fgg484-3", _io)
        pins = {
          'ProgPin': 'PullUp',
          'DonePin': 'PullUp',
          'TckPin': 'PullNone',
          'TdiPin': 'PullNone',
          'TdoPin': 'PullNone',
          'TmsPin': 'PullNone',
          'UnusedPin': 'PullNone',
          }
        for pin, config in pins.items():
            self.toolchain.bitgen_opt += " -g %s:%s " % (pin, config)
        self.add_platform_command("""CONFIG VCCAUX="3.3";""")

    def create_programmer(self):
        return iMPACT()
