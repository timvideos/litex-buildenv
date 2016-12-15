#!/usr/bin/env python3

import argparse
import os

from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)

    parser.add_argument("--platform", action="store", default=os.environ.get('PLATFORM', None))
    parser.add_argument("--target", action="store", default=os.environ.get('TARGET', None))
    parser.add_argument("--iprange", default="192.168.100")

    args = parser.parse_args()
    assert args.platform is not None
    assert args.target is not None

    exec("from {}_platform import Platform".format(args.platform), globals())
    platform = Platform()

    soc_name = "{}_{}".format(args.platform, args.target.lower())
    exec("from {} import {}SoC as SoC".format(soc_name, args.target), globals())
    soc = SoC(platform, **soc_sdram_argdict(args))

    if hasattr(soc, 'configure_iprange'):
        soc.configure_iprange(args.iprange)

    builddir = "build/{}_{}/".format(soc_name, args.cpu_type)
    testdir = "{}/test".format(builddir)

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
