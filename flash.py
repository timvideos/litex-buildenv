#!/usr/bin/env python3

import os
import argparse

import make


def main():
    parser = argparse.ArgumentParser(description="Board flashing tool")
    make.get_args(parser)

    parser.add_argument("--mode", default="image", choices=["image", "gateware", "bios", "firmware", "other"], help="Type of file to flash")
    parser.add_argument("--other-file", default=None)
    parser.add_argument("--address", type=int, help="Where to flash if using --mode=other")

    args = parser.parse_args()

    builddir = make.get_builddir(args)
    platform = make.get_platform(args)

    if args.mode == 'image':
        filename = make.get_image(builddir, "flash")
        address_start = 0
        address_end = platform.spiflash_total_size

    elif args.mode == 'gateware':
        filename = make.get_gateware(builddir, "flash")
        address_start = 0
        address_end = platform.gateware_size

    elif args.mode == 'bios':
        filename = make.get_bios(builddir, "flash")
        address_start = platform.gateware_size
        address_end = platform.gateware_size + make.BIOS_SIZE

    elif args.mode == 'firmware':
        if args.override_firmware:
            filename = args.override_firmware
        else:
            filename = make.get_firmware(builddir, "flash")

        address_start = platform.gateware_size + make.BIOS_SIZE
        address_end = platform.spiflash_total_size

    elif args.mode == 'other':
        filename = args.other_file
        address_start = args.address
        address_end = platform.spiflash_total_size

    else:
        assert False, "Unknown flashing mode."

    filepath = os.path.realpath(filename)

    assert address_start >= 0
    assert os.path.exists(filepath), "%s not found at %s" % (
            args.mode, filepath)

    file_size = len(open(filepath, 'rb').read())

    file_end = address_start+file_size
    assert file_end < address_end, "File is too big!\n%s file doesn't fit in %s space (%s extra bytes)." % (
        filename, file_size, address_end - address_start)

    prog = make.get_prog(args, platform)
    prog.flash(address_start, filepath)


if __name__ == "__main__":
    main()
