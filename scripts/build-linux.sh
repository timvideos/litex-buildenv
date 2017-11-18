#!/bin/bash

if [ "$(whoami)" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SCRIPT_SRC=$(realpath ${BASH_SOURCE[0]})
SCRIPT_DIR=$(dirname $SCRIPT_SRC)
TOP_DIR=$(realpath $SCRIPT_DIR/..)

if [ $SOURCED = 1 ]; then
        echo "You must run this script, rather then try to source it."
        echo "$SCRIPT_SRC"
        return
fi

if [ -z "$HDMI2USB_ENV" ]; then
        echo "You appear to not be inside the HDMI2USB environment."
	echo "Please enter environment with:"
	echo "  source scripts/enter-env.sh"
        exit 1
fi

# Imports TARGET, PLATFORM, CPU and TARGET_BUILD_DIR from Makefile
export FIRMWARE=linux
eval $(make env)
make info

set -x
set -e

if [ "$CPU" != or1k ]; then
	echo "Linux is only supported on or1k at the moment."
	exit 1
fi

(
	cd third_party/litex
	git checkout or1k-linux
)

make gateware

# Install a toolchain with the newlib standard library
if ! $CPU-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-$CPU-elf-newlib
fi

# Get linux-litex is needed
LINUX_SRC_DIR=$TOP_DIR/third_party/linux
if [ ! -d "$LINUX_SRC_DIR" ]; then
	(
		cd $(dirname $LINUX_SRC_DIR)
		git clone https://github.com/mithro/linux-litex.git -b litex-minimal linux
		cd $LINUX_SRC_DIR
		wget "https://drive.google.com/a/mithis.com/uc?authuser=0&id=0B5VlNZ_Rvdw6d21LWXdHQlZuOVU&export=download" -O openrisc-rootfs.cpio
		gzip openrisc-rootfs.cpio
	)
fi

# Build linux-litex
export ARCH=openrisc
export CROSS_COMPILE=$CPU-elf-newlib-
(
	cd $LINUX_SRC_DIR
	make litex_defconfig
	make -j32
	ls -l arch/openrisc/boot/vmlinux.bin
	mkdir -p $(dirname $TOP_DIR/$FIRMWARE_FILEBASE)
	cp arch/openrisc/boot/vmlinux.bin $TOP_DIR/$FIRMWARE_FILEBASE.bin
)
