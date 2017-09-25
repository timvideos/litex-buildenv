#!/bin/bash

if [ "`whoami`" = "root" ]
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
eval $(make env)
make info

set -x
set -e

# Install a toolchain with the newlib standard library
if ! $CPU-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-$CPU-elf-newlib
fi

# Get micropython is needed
MPY_SRC_DIR=$TOP_DIR/third_party/micropython
if [ ! -d "$MPY_SRC_DIR" ]; then
	(
		cd $(dirname $MPY_SRC_DIR)
		git clone https://github.com/upy-fpga/micropython.git
		cd $MPY_SRC_DIR
		git submodule update --init
	)
fi

# Generate the bios and local firmware
if [ ! -d $TARGET_BUILD_DIR/software/include/generated ]; then
	make firmware
fi

# Setup the micropython build directory
TARGET_MPY_BUILD_DIR=$TARGET_BUILD_DIR/software/micropython
if [ ! -e "$TARGET_MPY_BUILD_DIR/generated" ]; then
	mkdir -p $TARGET_MPY_BUILD_DIR
	(
		cd $TARGET_MPY_BUILD_DIR
		ln -s $(realpath $PWD/../../software/include/generated) generated
	)
fi
TARGET_MPY_BUILD_DIR="$(realpath $TARGET_BUILD_DIR/software/micropython)"

# Build micropython
export CROSS_COMPILE=$CPU-elf-newlib-
export BUILDINC_DIRECTORY="$(realpath $TARGET_BUILD_DIR/software/include)"
export BUILD="$(realpath $TARGET_MPY_BUILD_DIR)"
OLD_DIR=$PWD
cd $TARGET_MPY_BUILD_DIR
make V=1 -C $(realpath ../../../../third_party/micropython/litex/)
cd $OLD_DIR

# Generate a firmware image suitable for flashing.
python -m litex.soc.tools.mkmscimg -f $TARGET_MPY_BUILD_DIR/firmware.bin -o $TARGET_MPY_BUILD_DIR/firmware.fbi
/usr/bin/env python mkimage.py $MISOC_EXTRA_CMDLINE $LITEX_EXTRA_CMDLINE --output-file=$TARGET_BUILD_DIR/micropython.bin --override-firmware=$TARGET_MPY_BUILD_DIR/firmware.fbi
