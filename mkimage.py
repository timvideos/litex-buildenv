#!/usr/bin/env python3
"""
Flash image creation tool.
"""

import os
import argparse

import make


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
        if args.override_firmware.lower() == "none":
            firmware = None
        else:
            firmware = args.override_firmware
    if firmware:
        assert os.path.exists(firmware), (
            "Firmware file %r not found! "
            "Use --override-firmware=none for no firmware." % firmware)
        assert firmware.endswith('.fbi'), (
            "Firmware must be a MiSoC .fbi image.")

    platform = make.get_platform(args)

    gateware_pos = 0
    bios_pos = platform.gateware_size
    firmware_pos = platform.gateware_size + make.BIOS_SIZE

    print()
    with open(output_file, "wb") as f:
        # FPGA gateware
        if gateware:
            gateware_data = open(gateware, "rb").read()
        else:
            gateware_data = b""
            gateware = "Skipped"

        print(("Gateware @ 0x{:08x} ({:10} bytes) {:60}"
               " - Xilinx FPGA Bitstream"
               ).format(gateware_pos, len(gateware_data), gateware))
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
        assert len(bios_data) < make.BIOS_SIZE
        f.seek(bios_pos)
        f.write(bios_data)
        print(("    BIOS @ 0x{:08x} ({:10} bytes) {:60}"
               " - LiteX BIOS with CRC"
               ).format(bios_pos, len(bios_data), bios))
        print(" ".join("{:02x}".format(i) for i in bios_data[:64]))

        if firmware:
            firmware_data = open(firmware, "rb").read()
        else:
            firmware_data = b""
            firmware = "Skipped"

        # SoftCPU firmware
        print(("Firmware @ 0x{:08x} ({:10} bytes) {:60}"
               " - {} Firmware in FBI format (loaded into DRAM)"
               ).format(
                   firmware_pos, len(firmware_data), firmware,
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
            if args.force_image_size.lower() in ("true", "1"):
                flash_size = platform.spiflash_total_size
            else:
                flash_size = int(args.force_image_size)
            f.write(b'\xff' * (flash_size - f.tell()))

    print()
    print("Flash image: {}".format(output_file))
    flash_image_data = open(output_file, "rb").read()
    print(" ".join("{:02x}".format(i) for i in flash_image_data[:64]))


if __name__ == "__main__":
    main()
