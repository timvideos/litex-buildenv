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

#set -x
set -e

if [ "$CPU_VARIANT" != "linux" ]; then
	echo "Linux needs a CPU_VARIANT set to 'linux' to enable features"
	echo "needed by Linux like the MMU."
	exit 1
fi
if [ "$FIRMWARE" != "linux" ]; then
	echo "When building Linux you should set FIRMWARE to 'linux'."
	exit 1
fi

# Install a baremetal toolchain with the newlib standard library
if ! ${CPU_ARCH}-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-${CPU_ARCH}-elf-newlib
fi
# Install a Linux userspace toolchain with the musl standard library
if ! ${CPU_ARCH}-linux-musl-gcc --version > /dev/null 2>&1; then
	conda install gcc-${CPU_ARCH}-linux-musl
fi

if [ ${CPU} = mor1kx ]; then
	LINUX_REMOTE="${LINUX_REMOTE:-https://github.com/timvideos/linux-litex.git}"
	LINUX_REMOTE_NAME=timvideos-linux-litex
	LINUX_BRANCH=${LINUX_BRANCH:-master-litex}

	export ARCH=openrisc
	# To rebuild, use https://ozlabs.org/~joel/litex_or1k_defconfig
	ROOTFS_LOCATION="https://ozlabs.org/~joel/"
	ROOTFS=${ARCH}-rootfs.cpio.gz
elif [ ${CPU} = vexriscv ]; then
	LINUX_REMOTE="${LINUX_REMOTE:-https://github.com/torvalds/linux.git}"
	LINUX_REMOTE_NAME=upstream-linux
	LINUX_BRANCH=${LINUX_BRANCH:-v5.0}

	export ARCH=riscv
	ROOTFS_LOCATION="https://antmicro.com/projects/renode/litex-buildenv/"
	ROOTFS=${ARCH}32-rootfs.cpio
else
	echo "Linux is only supported on mor1kx or vexriscv at the moment."
	exit 1
fi

# Get linux-litex is needed
LINUX_SRC="$TOP_DIR/third_party/linux"
LINUX_LOCAL="$LINUX_GITLOCAL" # Local place to clone from
LINUX_REMOTE_BIT=$(echo $LINUX_REMOTE | sed -e's-^.*://--' -e's/.git$//')
LINUX_CLONE_FROM="${LINUX_LOCAL:-$LINUX_REMOTE}"
(
	# Download the Linux source for the first time
	if [ ! -d "$LINUX_SRC" ]; then
	(
		cd $(dirname $LINUX_SRC)
		echo "Downloading Linux source tree."
		echo "If you already have a local git checkout you can set 'LINUX_GITLOCAL' to speed up this step."
		git clone $LINUX_CLONE_FROM $LINUX_SRC --branch $LINUX_BRANCH
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
		if git rev-parse --abbrev-ref $LINUX_BRANCH > /dev/null 2>&1; then
			git checkout $LINUX_BRANCH
		else
			git checkout "$CURRENT_LINUX_REMOTE_NAME/$LINUX_BRANCH" -b $LINUX_BRANCH
		fi
	fi
)

# Get litex-devicetree
LITEX_DT_SRC="$TOP_DIR/third_party/litex-devicetree"
LITEX_DT_REMOTE="${LITEX_DT_REMOTE:-https://github.com/timvideos/litex-devicetree.git}"
LITEX_DT_REMOTE_BIT=$(echo $LITEX_DT_REMOTE | sed -e's-^.*://--' -e's/.git$//')
LITEX_DT_REMOTE_NAME=timvideos-litex-devicetree
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

# Build VexRiscv's emulator
if [ ${CPU} = vexriscv ]; then
	(
		cd $TOP_DIR

		GENERATED_MEM_HEADERS="$TARGET_BUILD_DIR/software/include/generated/mem.h"
		if [ ! -f "$GENERATED_MEM_HEADERS" ]; then
			make firmware
		fi

		source $SCRIPT_DIR/build-common.sh
		EMULATOR_RAM_BASE_ADDRESS=$(parse_generated_header "mem.h" EMULATOR_RAM_BASE)
		RAM_BASE_ADDRESS=$(parse_generated_header "mem.h" MAIN_RAM_BASE)
		# get rid of 'L' suffix
		RAM_BASE_ADDRESS=${RAM_BASE_ADDRESS::-1}
	 	EMULATOR_RAM_BASE_ADDRESS=${EMULATOR_RAM_BASE_ADDRESS::-1}

		cd $TOP_DIR/third_party/litex/litex/soc/cores/cpu/vexriscv/verilog/ext/VexRiscv/src/main/c/emulator

		# offsets are hardcoded in BIOS
		export CFLAGS="-DDTB=$((RAM_BASE_ADDRESS + 0x01000000)) -Wl,--defsym,__ram_origin=$EMULATOR_RAM_BASE_ADDRESS"
		export LITEX_BASE="$TOP_DIR/$TARGET_BUILD_DIR"
		export RISCV_BIN="${CPU_ARCH}-elf-newlib-"
		make clean
		make litex

		EMULATOR_BUILD_DIR="$TOP_DIR/$TARGET_BUILD_DIR/emulator"
		mkdir -p "$EMULATOR_BUILD_DIR"
		cp build/emulator.bin "$EMULATOR_BUILD_DIR"
	)
fi

# Build linux-litex
export CROSS_COMPILE=${CPU_ARCH}-linux-musl-

TARGET_LINUX_BUILD_DIR=$(dirname $TOP_DIR/$FIRMWARE_FILEBASE)
(
	cd $LINUX_SRC
	echo "Building Linux in $TARGET_LINUX_BUILD_DIR"
	mkdir -p $TARGET_LINUX_BUILD_DIR

	if [ ! -e $TARGET_LINUX_BUILD_DIR/$ROOTFS ]; then
		wget $ROOTFS_LOCATION/$ROOTFS -O $TARGET_LINUX_BUILD_DIR/$ROOTFS
	fi

	if [ ${CPU} = mor1kx ]; then
		KERNEL_BINARY=vmlinux.bin
		make O="$TARGET_LINUX_BUILD_DIR" litex_defconfig
	elif [ ${CPU} = vexriscv ]; then
		if [ ! -f $TARGET_LINUX_BUILD_DIR/.config ]; then
			wget ${ROOTFS_LOCATION}/litex_vexriscv_linux.config -O $TARGET_LINUX_BUILD_DIR/.config
		fi

		if [ ! -f $TARGET_LINUX_BUILD_DIR/rv32.dtb ]; then
			wget ${ROOTFS_LOCATION}/rv32.dtb -O $TARGET_LINUX_BUILD_DIR/rv32.dtb
		fi

		KERNEL_BINARY=Image
		make O="$TARGET_LINUX_BUILD_DIR" olddefconfig
	fi

	time make O="$TARGET_LINUX_BUILD_DIR" -j$JOBS
	ls -l $TARGET_LINUX_BUILD_DIR/arch/${ARCH}/boot/${KERNEL_BINARY}
	ln -sf $TARGET_LINUX_BUILD_DIR/arch/${ARCH}/boot/${KERNEL_BINARY} $TOP_DIR/$FIRMWARE_FILEBASE.bin
)
