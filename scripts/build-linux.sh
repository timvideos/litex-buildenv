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
eval $(make env)
make info

set -x
set -e

if [ "$CPU" != or1k ]; then
	echo "Linux is only supported on or1k at the moment."
	exit 1
fi
if [ "$CPU_VARIANT" != "linux" ]; then
	echo "Linux needs a CPU_VARIANT set to 'linux' to enable features"
	echo "needed by Linux like the MMU."
	exit 1
fi
if [ "$FIRMWARE" != "linux" ]; then
	echo "When building Linux you should set FIRMWARE to 'linux'."
	exit 1
fi

# Install a toolchain with the newlib standard library
if ! $CPU-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-$CPU-elf-newlib
fi

# Get linux-litex is needed
LINUX_SRC="$TOP_DIR/third_party/linux"
LINUX_LOCAL="$LINUX_GITLOCAL" # Local place to clone from
LINUX_REMOTE="${LINUX_REMOTE:-https://github.com/mithro/linux-litex.git}"
LINUX_REMOTE_NAME=mithro-linux-litex
LINUX_REMOTE_BIT=$(echo $LINUX_REMOTE | sed -e's-^.*://--' -e's/.git$//')
LINUX_CLONE_FROM="${LINUX_LOCAL:-$LINUX_REMOTE}"
LINUX_BRANCH=${LINUX_BRANCH:-litex-minimal}
(
	# Download the Linux source for the first time
	if [ ! -d "$LINUX_SRC" ]; then
	(
		cd $(dirname $LINUX_SRC)
		echo "Downloading Linux source tree."
		echo "If you already have a local git checkout you can set 'LINUX_GITLOCAL' to speed up this step."
		git clone $LINUX_CLONE_FROM $LINUX_SRC
	)
	fi

	# Change into the dir
	cd $LINUX_SRC

	# Add the remote if it doesn't exist
	CURRENT_LINUX_REMOTE_NAME=$(git remote -v | grep fetch | grep "$LINUX_REMOTE_BIT" | sed -e's/\t.*$//')
	if [ x"$CURRENT_LINUX_REMOTE_NAME" = x ]; then
		git remote add $LINUX_REMOTE_NAME $LINUX_REMOTE
		CURRENT_LINUX_REMOTE_NAME=$LINUX_REMOTE_NAME
	fi

	# Get any new data
	git fetch $CURRENT_LINUX_REMOTE_NAME

	# Checkout or1k-linux branch it not already on it
	if [ "$(git rev-parse --abbrev-ref HEAD)" != "$LINUX_BRANCH" ]; then
		git checkout $LINUX_BRANCH || \
			git checkout "$CURRENT_LINUX_REMOTE_NAME/$LINUX_BRANCH" -b $LINUX_BRANCH
	fi
)

# Get litex-devicetree
LITEX_DT_SRC="$TOP_DIR/third_party/litex-devicetree"
LITEX_DT_REMOTE="${LITEX_DT_REMOTE:-https://github.com/mithro/litex-devicetree.git}"
LITEX_DT_REMOTE_BIT=$(echo $LITEX_DT_REMOTE | sed -e's-^.*://--' -e's/.git$//')
LITEX_DT_REMOTE_NAME=mithro-litex-devicetree
LITEX_DT_BRANCH=master
(
	# Download the Linux source for the first time
	if [ ! -d "$LITEX_DT_SRC" ]; then
	(
		cd $(dirname $LITEX_DT_SRC)
		echo "Downloading LiteX devicetree code."
		git clone $LITEX_DT_REMOTE $LITEX_DT_SRC
	)
	fi

	# Change into the dir
	cd $LITEX_DT_SRC

	# Add the remote if it doesn't exist
	CURRENT_LITEX_DT_REMOTE_NAME=$(git remote -v | grep fetch | grep "$LITEX_DT_REMOTE_BIT" | sed -e's/\t.*$//')
	if [ x"$CURRENT_LITEX_DT_REMOTE_NAME" = x ]; then
		git remote add $LITEX_DT_REMOTE_NAME $LITEX_DT_REMOTE
		CURRENT_LITEX_DT_REMOTE_NAME=$LITEX_DT_REMOTE_NAME
	fi

	# Get any new data
	git fetch $CURRENT_LITEX_DT_REMOTE_NAME

	# Checkout or1k-linux branch it not already on it
	if [ "$(git rev-parse --abbrev-ref HEAD)" != "$LITEX_DT_BRANCH" ]; then
		git checkout $LITEX_DT_BRANCH || \
			git checkout "$CURRENT_LITEX_DT_REMOTE_NAME/$LITEX_DT_BRANCH" -b $LITEX_DT_BRANCH
	fi
)

# Build linux-litex
export ARCH=openrisc
export CROSS_COMPILE=$CPU-elf-newlib-
TARGET_LINUX_BUILD_DIR=$(dirname $TOP_DIR/$FIRMWARE_FILEBASE)
(
	cd $LINUX_SRC
	echo "Building Linux in $TARGET_LINUX_BUILD_DIR"
	mkdir -p $TARGET_LINUX_BUILD_DIR
	(
		cd $TARGET_LINUX_BUILD_DIR
		# To rebuild, use https://ozlabs.org/~joel/litex_or1k_defconfig
		ROOTFS=openrisc-rootfs.cpio.gz
		if [ ! -e $ROOTFS ]; then
			wget "https://ozlabs.org/~joel/openrisc-rootfs.cpio.gz" -O $ROOTFS
		fi
	)
	make O="$TARGET_LINUX_BUILD_DIR" litex_defconfig
	time make O="$TARGET_LINUX_BUILD_DIR" -j$JOBS
	ls -l $TARGET_LINUX_BUILD_DIR/arch/openrisc/boot/vmlinux.bin
	ln -sf $TARGET_LINUX_BUILD_DIR/arch/openrisc/boot/vmlinux.bin $TOP_DIR/$FIRMWARE_FILEBASE.bin
)
