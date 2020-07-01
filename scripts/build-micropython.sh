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
eval $(make --silent env)
make info

set -x
set -e

if [ "$FIRMWARE" != "micropython" ]; then
        echo "When building MicroPython you should set FIRMWARE to 'micropython'."
        exit 1
fi

# Install a toolchain with the newlib standard library
if ! ${CPU_ARCH}-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-${CPU_ARCH}-elf-newlib
fi

# Get micropython is needed
MPY_SRC_DIR=$TOP_DIR/third_party/micropython
if [ ! -d "$MPY_SRC_DIR" ]; then
	(
		cd $(dirname $MPY_SRC_DIR)
		git clone --branch new_litex https://github.com/antmicro/micropython.git
		cd $MPY_SRC_DIR
		git submodule update --init
	)
fi

# Generate the bios and local firmware
if [ ! -d $TARGET_BUILD_DIR/software/include/generated ]; then
	make firmware
fi

# Copy in some litex platform specific files that MicroPython may need
# in order to build; these need to end up in top level include directory
# so that they are found by compiler/assembler.
#
LITEX_INCLUDE_BASE="$PWD/third_party/litex/litex/soc/cores/cpu/$CPU"

for FILE in system.h csr-defs.h spr-defs.h; do
	# spr-defs.h is available only for selected CPUs
	if [ -e "$LITEX_INCLUDE_BASE/$FILE" ]; then
		cp -p "$LITEX_INCLUDE_BASE/$FILE" "$TARGET_BUILD_DIR/software/include"
	fi
done

# Setup the micropython build directory
TARGET_MPY_BUILD_DIR=$TARGET_BUILD_DIR/software/micropython
if [ ! -e "$TARGET_MPY_BUILD_DIR/generated" ]; then
	mkdir -p $TARGET_MPY_BUILD_DIR
	(
		cd $TARGET_MPY_BUILD_DIR
		ln -s $(realpath $PWD/../../software/include/generated) generated
	)
fi

if [ ! -e "$TARGET_MPY_BUILD_DIR/hw" ]; then
	(
		cd $TARGET_MPY_BUILD_DIR
		ln -s $(realpath $PWD/../../../../third_party/litex/litex/soc/software/include/hw) hw
	)
fi

if [ ! -e "$TARGET_MPY_BUILD_DIR/base" ]; then
	(
		cd $TARGET_MPY_BUILD_DIR
		ln -s $(realpath $PWD/../../../../third_party/litex/litex/soc/software/include/base) base
	)
fi

TARGET_MPY_BUILD_DIR="$(realpath $TARGET_BUILD_DIR/software/micropython)"

# Build micropython
export CROSS_COMPILE=${CPU_ARCH}-elf-newlib-
export BUILDINC_DIRECTORY="$(realpath $TARGET_BUILD_DIR/software/include)"
export BUILD="$(realpath $TARGET_MPY_BUILD_DIR)"
OLD_DIR=$PWD
cd $TARGET_MPY_BUILD_DIR
make V=1 -C $(realpath ../../../../third_party/micropython/ports/fupy/) -j$JOBS
cd $OLD_DIR

if [ -z "$SKIP_IMAGE" ]; then
	# Generate a firmware image suitable for flashing.
	make image
fi
