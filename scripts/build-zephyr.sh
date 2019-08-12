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
	exit 1
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

source $SCRIPT_DIR/settings.sh

# local version of SDK has a higher priority as it might contain a newer SDK
SDK_LOCAL_LOCATION="$BUILD_DIR/zephyr_sdk"
if [ -d "$SDK_LOCAL_LOCATION" ]; then
	export ZEPHYR_SDK_INSTALL_DIR="$SDK_LOCAL_LOCATION"
elif [ -z "$ZEPHYR_SDK_INSTALL_DIR" ]; then
	echo "Zephyr SDK not found"
	echo "Did you forget to run scripts/download-env.sh?"
	exit 1
fi

export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
echo "Using Zephyr SDK from: $ZEPHYR_SDK_INSTALL_DIR"

set -x
set -e

ZEPHYR_REPO=https://github.com/zephyrproject-rtos/zephyr
ZEPHYR_REPO_BRANCH=master

case $CPU in
	vexriscv)
		case "$CPU_VARIANT" in
			lite* | standard* | full* | linux*)
				TARGET_BOARD=litex_vexriscv
				;;
			*)
				echo "Zephyr needs a CPU_VARIANT set to at least 'lite' for the support of 'ecall' instruction."
				echo "Supported variants: lite, lite+debug, standard, standard+debug, full, full+debug, linux."
				echo "Currently selected variant: $CPU_VARIANT"
				exit 1
				;;
		esac
		;;
	*)
		echo "CPU $CPU isn't supported at the moment."
		exit 1
		;;
esac

if [ "$FIRMWARE" != "zephyr" ]; then
	echo "When building Zephyr you should set FIRMWARE to 'zephyr'."
	exit 1
fi

ZEPHYR_SRC_DIR=$THIRD_DIR/zephyr
ZEPHYR_APP=${ZEPHYR_APP:-subsys/shell/shell_module}
OUTPUT_DIR=$TOP_DIR/$TARGET_BUILD_DIR/software/zephyr
export ZEPHYR_BASE=$ZEPHYR_SRC_DIR/zephyr

if [ ! -d "$ZEPHYR_SRC_DIR" ]; then
	mkdir -p $ZEPHYR_SRC_DIR
	cd $ZEPHYR_SRC_DIR
	west init --manifest-url $ZEPHYR_REPO --manifest-rev $ZEPHYR_REPO_BRANCH
fi
west build -b $TARGET_BOARD $ZEPHYR_SRC_DIR/zephyr/samples/$ZEPHYR_APP --build-dir $OUTPUT_DIR -- -DZEPHYR_SDK_INSTALL_DIR=$ZEPHYR_SDK_INSTALL_DIR

cd $OUTPUT_DIR
if [ ! -f "firmware.bin" ]; then
	ln -s zephyr/zephyr.bin firmware.bin
fi

