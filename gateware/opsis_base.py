#!/usr/bin/env python3

import argparse
import os
import importlib

from litex.gen import *
from litex.gen.genlib.io import CRG

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.gpio import GPIOIn, GPIOOut
from litex.soc.interconnect.csr import AutoCSR

import opsis_platform


class CaseGPIO(Module, AutoCSR):
    def __init__(self, platform):
        switchs = Signal(2)
        leds = Signal(2)

        # # #

        self.submodules.switchs = GPIOIn(switchs)
        self.submodules.leds = GPIOOut(leds)

        hdled = platform.request("hdled")
        pwled = platform.request("pwled")
        rstsw = platform.request("rstsw")
        pwrsw = platform.request("pwrsw")
        self.comb += [
           rstsw.p.eq(1),
           pwrsw.p.eq(1),
           switchs[0].eq(rstsw.n),
           switchs[1].eq(pwrsw.n),
           hdled.p.eq(leds[0]),
           hdled.n.eq(~leds[0]),
           pwled.p.eq(leds[1]),
           pwled.n.eq(~leds[1]),
        ]


class BaseSoC(SoCCore):
    csr_map = {
        "case":      18,
        "user_leds": 19,
    }
    csr_map.update(SoCCore.csr_map)

    def __init__(self, platform, **kwargs):
        SoCCore.__init__(self, platform,
            clk_freq=int((1/(platform.default_clk_period))*1000000000),
            integrated_rom_size=0x8000,
            integrated_main_ram_size=0x8000,
            **kwargs)
        self.submodules.crg = CRG(platform.request(platform.default_clk_name))

        # case switches/leds
        self.submodules.case =  CaseGPIO(platform)

        # user leds
        self.submodules.user_leds = GPIOOut(Cat(platform.request("user_led", 0),
                                                platform.request("user_led", 1),
                                                platform.request("user_led", 2),
                                                platform.request("user_led", 3)))


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_core_args(parser)
    parser.add_argument("--build", action="store_true",
                        help="build bitstream")
    parser.add_argument("--load", action="store_true",
                        help="load bitstream")
    args = parser.parse_args()

    platform = opsis_platform.Platform()
    soc = BaseSoC(platform, **soc_core_argdict(args))
    builder = Builder(soc, **builder_argdict(args))

    if args.build:
        builder.build()

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.output_dir, "gateware", "top.bit"))

if __name__ == "__main__":
    main()
