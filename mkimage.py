#!/usr/bin/env python3

import argparse

from make import make_args, make_builddir, make_platform

BIOS_SIZE=0x8000

def main():
    parser = argparse.ArgumentParser(description="SPI Flash contents tool")
    make_args(parser)

    parser.add_argument("--override-gateware")
    parser.add_argument("--override-bios")
    parser.add_argument("--override-firmware")

    args = parser.parse_args()

    builddir = make_builddir(args)
    gateware = "{}/gateware/top.bin".format(builddir)
    if args.override_gateware:
        if args.override_gateware.lower() == "none":
            gateware = None
        else:
            gateware = args.override_gateware
    if gateware:
        assert os.path.exists(gateware), "Gateware file not found! Use --override-gateware=none for no gateware."

    bios = "{}/software/bios/bios.bin".format(builddir)
    if args.override_bios:
        if args.override_bios.lower() == "none":
            bios = None
        else:
            bios = args.override_bios
    if bios:
        assert os.path.exists(bios), "BIOS file not found! Use --override-bios=none for no BIOS."

    firmware = "{}/software/firmware/firmware.fbi".format(builddir)
    if args.override_firmware:
        if args.override_firmware.lower() == "none":
            firmware = None
        else:
            firmware = args.override_firmware
    if firmware:
        assert os.path.exists(firmware), "Firmware file not found! Use --override-firmware=none for no firmware."

    platform = make_platform(args)

    gateware_pos = 0
    bios_pos = platform.gateware_size
    firmware_pos = platform.gateware_size + BIOS_SIZE

    output = "{}/flash.bin".format(builddir)
    with open(output, "wb") as f:
        print()
        if gateware:
            gateware_data = open(gateware, "rb").read()
            print("Gateware @ 0x{:08x} ({:10} bytes) {:60} - Xilinx Bitstream".format(gateware_pos, len(gateware_data), gateware))
            print(" ".join("{:02x}".format(i) for i in gateware_data[:64]))
            assert len(gateware_data) < platform.gateware_size
            f.seek(0)
            f.write(gateware_data)
        else:
            print("Skipping gateware.")

        if bios:
            bios_data = open(bios, "rb").read()
            assert len(bios_data) < BIOS_SIZE
            print("    BIOS @ 0x{:08x} ({:10} bytes) {:60} - LiteX BIOS with CRC".format(bios_pos, len(bios_data), bios))
            print(" ".join("{:02x}".format(i) for i in bios_data[:64]))
            f.seek(bios_pos)
            f.write(bios_data)
        else:
            print("Skipping BIOS.")

        if firmware:
            firmware_data = open(firmware, "rb").read()
            print("Firmware @ 0x{:08x} ({:10} bytes) {:60} - HDMI2USB Firmware in FBI format (loaded into DRAM)".format(firmware_pos, len(firmware_data), firmware))
            print(" ".join("{:02x}".format(i) for i in firmware_data[:64]))
            f.seek(firmware_pos)
            f.write(firmware_data)
        else:
            print("Skipping firmware.")
            firmware_data=[]

        remain = platform.spiflash_total_size - (firmware_pos+len(firmware_data))
        print("-"*40)
        print("       Remaining space {:10} bytes ({} Megabits, {:.2f} Megabytes)".format(remain, int(remain*8/1024/1024), remain/1024/1024))
        total = platform.spiflash_total_size
        print("           Total space {:10} bytes ({} Megabits, {:.2f} Megabytes)".format(total, int(total*8/1024/1024), total/1024/1024))

    print()
    print("Flash image: {}".format(output))
    flash_image_data = open(output, "rb").read() 
    print(" ".join("{:02x}".format(i) for i in flash_image_data[:64]))

if __name__ == "__main__":
    main()
