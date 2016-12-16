#!/usr/bin/env python3

import argparse
import os

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *


def make_args(parser, platform='opsis', target='hdmi2usb'):
    parser.add_argument("--platform", action="store", default=os.environ.get('PLATFORM', platform))
    parser.add_argument("--target", action="store", default=os.environ.get('TARGET', target))
    parser.add_argument("--iprange", default="192.168.100")
    parser.add_argument("--cpu-type", default=os.environ.get('CPU', 'lm32'))


def make_builddir(args):
    return "build/{}_{}_{}/".format(args.platform, args.target.lower(), args.cpu_type)


def make_testdir(args):
    builddir = make_builddir(args)
    testdir = "{}/test".format(builddir)
    return testdir


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC", conflict_handler='resolve')
    make_args(parser)
    builder_args(parser)
    soc_sdram_args(parser)

    args = parser.parse_args()
    assert args.platform is not None
    assert args.target is not None

    exec("from platforms.{} import Platform".format(args.platform), globals())
    platform = Platform()

    exec("from targets.{}.{} import SoC".format(args.platform, args.target.lower(), args.target), globals())
    soc = SoC(platform, **soc_sdram_argdict(args))
    if hasattr(soc, 'configure_iprange'):
        soc.configure_iprange(args.iprange)

    builddir = make_builddir(args)
    testdir = make_testdir(args)

    buildargs = builder_argdict(args)
    if not buildargs.get('output_dir', None):
        buildargs['output_dir'] = builddir
    if not buildargs.get('csr_csv', None):
        buildargs['csr_csv'] = os.path.join(testdir, "csr.csv")

    builder = Builder(soc, **buildargs)
    builder.add_software_package("libuip", "{}/firmware/libuip".format(os.getcwd()))
    builder.add_software_package("firmware", "{}/firmware".format(os.getcwd()))
    vns = builder.build()


if __name__ == "__main__":
    main()
