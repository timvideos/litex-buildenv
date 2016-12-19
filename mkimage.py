#!/bin/bash


import argparse

from make import make_args, make_builddir, make_platform

BIOS_SIZE=0x8000

def main():
    parser = argparse.ArgumentParser(description="SPI Flash contents tool")
    make_args(parser)
    args = parser.parse_args()

    builddir = make_builddir(args)
    gateware = "{}/gateware/top.bin".format(builddir)
    bios = "{}/software/bios/bios.bin".format(builddir)
    firmware = "{}/software/firmware/firmware.fbi".format(builddir)

    platform = make_platform(args)

    gateware_pos = 0
    bios_pos = platform.gateware_size
    firmware_pos = platform.gateware_size + BIOS_SIZE

    output = "{}/flash.bin".format(builddir)
    with open(output, "wb") as f:
        print()
        gateware_data = open(gateware, "rb").read()
        print("Gateware @ 0x{:08x} ({:10} bytes) - Xilinx Bitstream".format(gateware_pos, len(gateware_data)))
        assert len(gateware_data) < platform.gateware_size
        f.seek(0)
        f.write(gateware_data)

        bios_data = open(bios, "rb").read()
        assert len(bios_data) < BIOS_SIZE
        print("    BIOS @ 0x{:08x} ({:10} bytes) - LiteX BIOS with CRC".format(bios_pos, len(bios_data)))
        f.seek(platform.gateware_size)
        f.write(bios_data)

        firmware_data = open(firmware, "rb").read()
        print("Firmware @ 0x{:08x} ({:10} bytes) - HDMI2USB Firmware in FBI format (loaded into DRAM)".format(firmware_pos, len(firmware_data)))
        f.seek(platform.gateware_size + BIOS_SIZE)
        f.write(firmware_data)

        remain = platform.spiflash_total_size - (firmware_pos+len(firmware_data))
        print("-"*40)
        print("       Remaining space {:10} bytes ({} Megabits, {:.2f} Megabytes)".format(remain, int(remain*8/1024/1024), remain/1024/1024))
        total = platform.spiflash_total_size
        print("           Total space {:10} bytes ({} Megabits, {:.2f} Megabytes)".format(total, int(total*8/1024/1024), total/1024/1024))

if __name__ == "__main__":
    main()
