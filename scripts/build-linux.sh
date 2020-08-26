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
eval $(make --silent env)
make info

set -x
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

LINUX_REMOTE="${LINUX_REMOTE:-https://github.com/litex-hub/linux.git}"
LINUX_REMOTE_NAME=litex-hub-linux
LINUX_BRANCH=${LINUX_BRANCH:-litex_buildenv}

RESOURCES_LOCATION="https://dl.antmicro.com/projects/renode/litex-buildenv/"

if [ ${CPU} = mor1kx ]; then
	export ARCH=openrisc
	ROOTFS=or1k-rootfs.cpio
	DTB=mor1kx.dtb
	ROOTFS_MD5="c9ef89b45b0d2c34d14978a21f2863bd"
elif [ ${CPU} = vexriscv ]; then
	export ARCH=riscv
	ROOTFS=riscv32-rootfs.cpio
	DTB=rv32.dtb
	ROOTFS_MD5="7b1a7fb52a1ba056dffb351a036bd0fb"
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


# Build VexRiscv's emulator
if [ ${CPU} = vexriscv ]; then
	(
		cd $TOP_DIR

		GENERATED_MEM_HEADERS="$TARGET_BUILD_DIR/software/include/generated/mem.h"
		if [ ! -f "$GENERATED_MEM_HEADERS" ]; then
			make firmware
		fi

		source $SCRIPT_DIR/build-common.sh
		RAM_BASE_ADDRESS=$(parse_generated_header "mem.h" MAIN_RAM_BASE)
		# get rid of 'L' suffix
		RAM_BASE_ADDRESS=${RAM_BASE_ADDRESS::-1}

		cd $TOP_DIR/third_party/VexRiscv/src/main/c/emulator

		# offsets are hardcoded in BIOS
		export CFLAGS="-DOS_CALL=$((RAM_BASE_ADDRESS + 0x0)) -DDTB=$((RAM_BASE_ADDRESS + 0x01000000)) -Wl,--defsym,__ram_origin=$((RAM_BASE_ADDRESS + 0x01100000)) -I$TOP_DIR/third_party/litex/litex/soc/cores/cpu/vexriscv"
		export LITEX_GENERATED="$TOP_DIR/$TARGET_BUILD_DIR/software/include"
		export LITEX_BASE="$TOP_DIR/third_party/litex"
		export RISCV_BIN="${CPU_ARCH}-elf-newlib-"
		make clean
		make litex

		EMULATOR_BUILD_DIR="$TOP_DIR/$TARGET_BUILD_DIR/emulator"
		mkdir -p "$EMULATOR_BUILD_DIR"
		cp build/emulator.bin "$EMULATOR_BUILD_DIR"
	)
fi

function calcualte_md5() {
	# will be '0' if the file does not exist
	(md5sum "$1" 2>/dev/null || echo "0") | cut -d' ' -f1
}

function fetch_file() {
	URL=$1
	EXPECTED_MD5=$2
	TRGT=$3

	ACTUAL_MD5=`calcualte_md5 $TRGT`

	if [ $ACTUAL_MD5 != $EXPECTED_MD5 ]; then
		wget $URL -O $TRGT

		ACTUAL_MD5=`calcualte_md5 $TRGT`
		if [ $ACTUAL_MD5 != $EXPECTED_MD5 ]; then
			echo "Could not fetch file from $URL"
			exit 1
		fi
	fi
}

# Build linux-litex
export CROSS_COMPILE=${CPU_ARCH}-linux-musl-

TARGET_LINUX_BUILD_DIR=$(dirname $TOP_DIR/$FIRMWARE_FILEBASE)

BD_REMOTE="${BD_REMOTE:-https://github.com/buildroot/buildroot.git}"
BD_SRC="$TOP_DIR/third_party/buildroot"
LLV_REMOTE="${LLV_REMOTE:-https://github.com/litex-hub/linux-on-litex-vexriscv.git}"
LLV_SRC="$TOP_DIR/third_party/linux-on-litex-vexriscv"
(
	cd $LINUX_SRC
	echo "Building Linux in $TARGET_LINUX_BUILD_DIR"
	mkdir -p $TARGET_LINUX_BUILD_DIR

	fetch_file $RESOURCES_LOCATION/$ROOTFS_MD5-$ROOTFS $ROOTFS_MD5 $TARGET_LINUX_BUILD_DIR/$ROOTFS

	if [ ${CPU} = mor1kx ]; then
		KERNEL_BINARY=vmlinux.bin

        	cat << EOF > $TARGET_LINUX_BUILD_DIR/boot.json
{
    "$DTB":         "0x01000000",
    "Image":        "0x00000000",
    "bootargs": {
        "r1":       "0x01000000"
    }
}
EOF
	elif [ ${CPU} = vexriscv ]; then
		KERNEL_BINARY=Image

        	cat << EOF > $TARGET_LINUX_BUILD_DIR/boot.json
{
    "Image":        "0x40000000",
    "rootfs.cpio":  "0x40800000",
    "$DTB":         "0x41000000",
    "emulator.bin": "0x41100000"
}
EOF
	fi

	make O="$TARGET_LINUX_BUILD_DIR" litex_defconfig
	time make O="$TARGET_LINUX_BUILD_DIR" -j$JOBS

	if [ ${CPU} = mor1kx ]; then
		${CROSS_COMPILE}objcopy -O binary $TARGET_LINUX_BUILD_DIR/vmlinux $TARGET_LINUX_BUILD_DIR/arch/${ARCH}/boot/${KERNEL_BINARY}
	fi

	ls -l $TARGET_LINUX_BUILD_DIR/arch/${ARCH}/boot/${KERNEL_BINARY}
	ln -sf $TARGET_LINUX_BUILD_DIR/arch/${ARCH}/boot/${KERNEL_BINARY} $TOP_DIR/$FIRMWARE_FILEBASE.bin
)

# Generate the device tree file
LITEX_CONFIG_JSON="$TARGET_BUILD_DIR/test/csr.json"
LITEX_DT_GENERATOR_FILE="$TOP_DIR/third_party/litex/litex/tools/litex_json2dts.py"
if [ ! -f "$LITEX_CONFIG_JSON" ]; then
	make firmware
fi

python $LITEX_DT_GENERATOR_FILE $LITEX_CONFIG_JSON | dtc -I dts -O dtb - > $TARGET_LINUX_BUILD_DIR/$DTB

