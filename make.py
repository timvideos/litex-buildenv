#!/usr/bin/env python3

import argparse
import os

from litex.build.tools import write_to_file
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *


def get_args(parser, platform='opsis', target='hdmi2usb'):
    parser.add_argument("--platform", action="store", default=os.environ.get('PLATFORM', platform))
    parser.add_argument("--target", action="store", default=os.environ.get('TARGET', target))

    soc_sdram_args(parser)
    parser.set_defaults(cpu_type=os.environ.get('CPU', 'lm32'))
    parser.set_defaults(cpu_variant=os.environ.get('CPU_VARIANT', None) or None)

    parser.add_argument("--iprange", default="192.168.100")

    parser.add_argument("-Op", "--platform-option", default=[], nargs=2, action="append", help="set platform-specific option")
    parser.add_argument("-Ot", "--target-option", default=[], nargs=2, action="append", help="set target-specific option")
    parser.add_argument("-Ob", "--build-option", default=[], nargs=2, action="append", help="set build option")

    parser.add_argument("--no-compile-firmware", action="store_true", help="do not compile the firmware")
    parser.add_argument("--override-firmware", action="store", default=None, help="override firmware with file")


def get_builddir(args):
    assert args.platform is not None
    assert args.target is not None
    assert args.cpu_type is not None
    full_platform = args.platform
    for name, value in args.target_option:
        if name == 'tofe_board':
            full_platform = "{}.{}".format(full_platform, value)
    full_cpu = args.cpu_type
    if args.cpu_variant:
        full_cpu = "{}.{}".format(full_cpu, args.cpu_variant)
    return "build/{}_{}_{}/".format(full_platform.lower(), args.target.lower(), full_cpu.lower())


def get_testdir(args):
    builddir = get_builddir(args)
    testdir = "{}/test".format(builddir)
    return testdir


def get_platform(args):
    assert args.platform is not None
    exec("from platforms.{} import Platform".format(args.platform), globals())
    return Platform(**dict(args.platform_option))


def get_soc(args, platform):
    exec("from targets.{}.{} import SoC".format(args.platform, args.target.lower(), args.target), globals())
    soc = SoC(platform, ident=SoC.__name__, **soc_sdram_argdict(args), **dict(args.target_option))
    if hasattr(soc, 'configure_iprange'):
        soc.configure_iprange(args.iprange)
    return soc


def get_prog(args, platform):
    assert platform is not None
    prog = platform.create_programmer()
    prog.set_flash_proxy_dir(os.path.join("third_party","flash_proxies"))
    return prog


def get_image(builddir, filetype):
    assert filetype == "flash"
    return os.path.join(builddir, "image.bin")


def get_gateware(builddir, filetype):
    basedir = os.path.join(builddir, "gateware", "top")
    if filetype in ("load",):
        return basedir + ".bit"
    elif filetype in ("flash",):
        return basedir + ".bin"


def get_bios(builddir, filetype="flash"):
    basedir = os.path.join(builddir, "software", "bios", "bios")
    if filetype in ("load", "flash"):
        return basedir + ".bin"
    elif filetype in ("debug",):
        return basedir + ".elf"
    else:
        assert False, "Unknown file type %s" % filetype


def get_bios_maxsize(args, soc):
    for name, region in soc.mem_regions.items():
        if name == 'rom':
            return region.length
    # FIXME: Hard coded value?
    return 0x8000


def get_firmware(builddir, filetype="flash"):
    basedir = os.path.join(builddir, "software", "firmware", "firmware")
    if filetype in ("load",):
        return basedir + ".bin"
    elif filetype in ("flash",):
        return basedir + ".fbi"
    elif filetype in ("debug",):
        return basedir + ".elf"
    else:
        assert False, "Unknown file type %s" % filetype


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC", conflict_handler='resolve')
    get_args(parser)
    builder_args(parser)
    soc_sdram_args(parser)

    args = parser.parse_args()

    platform = get_platform(args)

    soc = get_soc(args, platform)

    builddir = get_builddir(args)
    testdir = get_testdir(args)

    buildargs = builder_argdict(args)
    if not buildargs.get('output_dir', None):
        buildargs['output_dir'] = builddir

    if hasattr(soc, 'cpu_type'):
        if not buildargs.get('csr_csv', None):
            buildargs['csr_csv'] = os.path.join(testdir, "csr.csv")

        if not buildargs.get('csr_json', None):
            buildargs['csr_json'] = os.path.join(testdir, "csr.json")

        builder = Builder(soc, **buildargs)
        if not args.no_compile_firmware or args.override_firmware:
            builder.add_software_package("uip", "{}/firmware/uip".format(os.getcwd()))

            # FIXME: All platforms which current run their user programs from
            # SPI flash lack the block RAM resources to run the default
            # firmware. Check whether to use the stub or default firmware
            # should be refined (perhaps soc attribute?).
            if "main_ram" in soc.mem_regions:
                builder.add_software_package("firmware", "{}/firmware".format(os.getcwd()))
            else:
                builder.add_software_package("stub", "{}/firmware/stub".format(os.getcwd()))
        vns = builder.build(**dict(args.build_option))
    else:
        vns = platform.build(soc, build_dir=os.path.join(builddir, "gateware"))

    if hasattr(soc, 'pcie_phy'):
        from targets.common import cpu_interface
        csr_header = cpu_interface.get_csr_header(soc.get_csr_regions(), soc.get_constants())
        kerneldir = os.path.join(builddir, "software", "pcie", "kernel")
        os.makedirs(kerneldir, exist_ok=True)
        write_to_file(os.path.join(kerneldir, "csr.h"), csr_header)

    if hasattr(soc, 'do_exit'):
        soc.do_exit(vns, filename="{}/analyzer.csv".format(testdir))


if __name__ == "__main__":
    main()
