#!/usr/bin/env python3
"""
Flash image creation tool.
"""

import os
import argparse

import make

from collections import namedtuple
from targets.utils import round_up_to_4


_Region = namedtuple("Region", ["name", "desc", "start", "size"])
class Region(_Region):
    def __init__(self, name, desc, start, size):
        #_Region.__init__(self, name, start, size, desc)
        assert round_up_to_4(start) == start, (
            "Start invalid {} != {}".format(start, round_up_to_4(start)))
        assert round_up_to_4(size) == size, (
            "Size invalid {} != {}".format(size, round_up_to_4(size)))

    def __str__(self):
        return "Region(0x{:06x}, 0x{:06x}, {:10s}, {})".format(
            self.start, self.end, repr(self.name), repr(self.desc))

    @property
    def end(self):
        return self.start + self.size


def get_regions(size_gw, size_bios, size_flash):
    """

    >>> regions = get_regions(256, 128, 1000)
    >>> for r in regions:
    ...     print(r)
    Region(0x000000, 0x000100, 'Gateware', 'FPGA bitstream')
    Region(0x000100, 0x000180, 'BIOS'    , 'LiteX BIOS with CRC')
    Region(0x000180, 0x0003e8, 'Firmware', 'Firmware in FBI format')

    """
    region_gw = Region(
        "Gateware",
        "FPGA bitstream",
        0,
        round_up_to_4(size_gw),
    )
    region_bios = Region(
        "BIOS",
        "LiteX BIOS with CRC",
        region_gw.end,
        size_bios,
    )
    size_fw = round_up_to_4(size_flash - region_bios.end)
    region_fw = Region(
        "Firmware",
        "Firmware in FBI format",
        region_bios.end,
        size_fw,
    )
    return [region_gw, region_bios, region_fw]


def fill_region(image_fileobj, region, input_filename, fill_zero=False):
    """

    Output;
    -----
    Gateware @ 0x00000000 (using      135100 bytes of     163840 bytes) build/ice40_hx8k_b_evn_base_vexriscv.minimal+debug//gateware/top.bin - FPGA Bitstream
    ff 00 00 ff 7e aa 99 7e 51 00 01 05 92 00 21 62 03 67 72 01 10 82 00 00 11 00 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    -----

    {name  } @ {start   } (using {input_len} bytes of {length  } bytes) {input_fn} - {desc}
    {hex file data}
    """

    if inputfile:
        input_data   = open(input_filename, "rb").read()
        input_size   = len(input_data)
        input_result = "Loaded from {}".format(input_filename)
    else:
        input_data   = b""
        input_size   = len(input_data)
        input_result = "Skipped"

    #   "{name:08s} @ 0x{start:08x} "
    #   "(using {input_size:10} bytes of {:10} bytes - {:02.2)%) {:60s} - {}"

    #print(
    #    "{:08s} @ 0x{:08x} (using {:10} bytes of {:10} bytes - {:02.2)% {:60s} - {}"
    #).format()

    print(" ".join("{:02x}".format(i) for i in input_data[:64]))
    assert input_size < region.size
    assert f.tell() < region.start, "{} < {}".format(f.tell(), region.start)
    f.seek(region.start)
    f.write(input_data)
    if fill_zero:
        while f.tell() < region.end:
            f.write('\0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    make.get_args(parser)

    parser.add_argument("--output-file", default="image.bin")
    parser.add_argument("--override-gateware")
    parser.add_argument("--override-bios")
    parser.add_argument("--firmware-name", default="HDMI2USB")
    parser.add_argument("--force-image-size")

    args = parser.parse_args()

    builddir = make.get_builddir(args)
    if os.path.sep not in args.output_file:
        args.output_file = os.path.join(builddir, args.output_file)

    output_file = args.output_file
    output_dir = os.path.dirname(output_file)
    assert os.path.exists(output_dir), (
        "Directory %r doesn't exist!" % output_dir)

    gateware = make.get_gateware(builddir, "flash")
    if args.override_gateware:
        if args.override_gateware.lower() == "none":
            gateware = None
        else:
            gateware = args.override_gateware
    if gateware:
        assert os.path.exists(gateware), (
            "Gateware file %r not found! "
            "Use --override-gateware=none for no gateware." % gateware)
        assert gateware.endswith('.bin'), (
            "Gateware must be a .bin for flashing (not %s)." % gateware)

    bios = make.get_bios(builddir, "flash")
    if args.override_bios:
        if args.override_bios.lower() == "none":
            bios = None
        else:
            bios = args.override_bios
    if bios:
        assert os.path.exists(bios), (
            "BIOS file %r not found! "
            "Use --override-bios=none for no BIOS." % bios)

    firmware = make.get_firmware(builddir, "flash")
    if args.override_firmware:
        if args.override_firmware.lower() in ("none", "clear"):
            firmware = None
            args.firmware_name = args.override_firmware
        else:
            firmware = args.override_firmware
    if firmware:
        assert os.path.exists(firmware), (
            "Firmware file %r not found! "
            "Use --override-firmware=none for no firmware." % firmware)
        assert firmware.endswith('.fbi'), (
            "Firmware must be a MiSoC .fbi image.")

    platform = make.get_platform(args)
    soc = make.get_soc(args, platform)
    bios_size = make.get_bios_maxsize(args, soc)

    gateware_pos = 0
    bios_pos = platform.gateware_size
    firmware_pos = platform.gateware_size + bios_size

    flash_size = platform.spiflash_total_size
    if args.force_image_size and args.force_image_size.lower() not in ("true", "1"):
            flash_size = int(args.force_image_size)

    print()
    with open(output_file, "wb") as f:
        # FPGA gateware
        if gateware:
            gateware_data = open(gateware, "rb").read()
        else:
            gateware_data = b""
            gateware = "Skipped"

        print(("Gateware @ 0x{:08x} (using {:10} bytes of {:10} bytes) {:60}"
               " - FPGA Bitstream"
               ).format(
                   gateware_pos,
                   len(gateware_data),
                   bios_pos - gateware_pos,
                   gateware))
        print(" ".join("{:02x}".format(i) for i in gateware_data[:64]))
        assert len(gateware_data) < platform.gateware_size
        f.seek(0)
        f.write(gateware_data)

        if bios:
            bios_data = open(bios, "rb").read()
        else:
            bios_data = b""
            bios = "Skipped"

        # LiteX BIOS
        assert len(bios_data) < bios_size
        f.seek(bios_pos)
        f.write(bios_data)
        print(("    BIOS @ 0x{:08x} (using {:10} bytes of {:10} bytes) {:60}"
               " - LiteX BIOS with CRC"
               ).format(
                   bios_pos,
                   len(bios_data),
                   firmware_pos - bios_pos,
                   bios))
        print(" ".join("{:02x}".format(i) for i in bios_data[:64]))

        if firmware:
            firmware_data = open(firmware, "rb").read()
        else:
            firmware_data = b"\xff\xff\xff\xff"
            firmware = "Cleared"
            #firmware_data = b""
            #firmware = "Skipped"

        # SoftCPU firmware
        print(("Firmware @ 0x{:08x} (using {:10} bytes of {:10} bytes) {:60}"
               " - {} Firmware in FBI format (loaded into DRAM)"
               ).format(
                   firmware_pos,
                   len(firmware_data),
                   flash_size - firmware_pos,
                   firmware,
                   args.firmware_name))
        print(" ".join("{:02x}".format(i) for i in firmware_data[:64]))
        f.seek(firmware_pos)
        f.write(firmware_data)

        # Result
        remain = platform.spiflash_total_size - (
            firmware_pos+len(firmware_data))
        print("-"*40)
        print(("       Remaining space {:10} bytes"
               " ({} Megabits, {:.2f} Megabytes)"
               ).format(remain, int(remain*8/1024/1024), remain/1024/1024))
        total = platform.spiflash_total_size
        print(("           Total space {:10} bytes"
               " ({} Megabits, {:.2f} Megabytes)"
               ).format(total, int(total*8/1024/1024), total/1024/1024))

        if args.force_image_size:
            f.write(b'\xff' * (flash_size - f.tell()))

    print()
    print("Flash image: {}".format(output_file))
    flash_image_data = open(output_file, "rb").read()
    print(" ".join("{:02x}".format(i) for i in flash_image_data[:64]))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    main()
