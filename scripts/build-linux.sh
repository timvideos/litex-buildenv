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

REMOTE_NAME=h2u-litex-linux

LITEX_SRC=$TOP_DIR/third_party/litex
LITEX_BRANCH=${LITEX_BRANCH:-or1k-linux}
LITEX_REMOTE="${LITEX_REMOTE:-https://github.com/enjoy-digital/litex.git}"
LITEX_REMOTE_BIT=$(echo $LITEX_REMOTE | sed -e's-^.*://--' -e's/.git$//')
(
	# Init the submodule if it doesn't exist
	if [ ! -d $LITEX_SRC ]; then
		git submodule update --init third_party/litex
	fi

	# Change into the dir
	cd $LITEX_SRC

	# Add the remote if it doesn't exist
	LITEX_REMOTE_NAME="$(git remote -v | grep fetch | grep "$LITEX_REMOTE_BIT" | sed -e's/\t.*$//')"
	if [ x"$LITEX_REMOTE_NAME" = x ]; then
		git remote add "$REMOTE_NAME" "$LITEX_REMOTE"
		LITEX_REMOTE_NAME=$REMOTE_NAME
	fi

	# Get any new data
	git fetch $LITEX_REMOTE_NAME

	# Checkout or1k-linux branch it not already on it
	if [ "$(git rev-parse --abbrev-ref HEAD)" != "$LITEX_BRANCH" ]; then
		git checkout $LITEX_BRANCH || \
			git checkout "$LITEX_REMOTE_NAME/$LITEX_BRANCH" -b $LITEX_BRANCH

		# Need to rebuild the gateware
		# FIXME: Make this conditional on the gateware /actually/ changing
		(
			cd $TOP_DIR
			make gateware
		)
	fi
)
# Unset these values as LITEX and LINUX are very close in name and hence could
# accidentally be used below.
unset LITEX_SRC
unset LITEX_BRANCH
unset LITEX_REMOTE
unset LITEX_REMOTE_BIT

# Install a toolchain with the newlib standard library
if ! $CPU-elf-newlib-gcc --version > /dev/null 2>&1; then
	conda install gcc-$CPU-elf-newlib
fi

# Get linux-litex is needed
LINUX_SRC="$TOP_DIR/third_party/linux"
LINUX_LOCAL="$LINUX_GITLOCAL" # Local place to clone from
LINUX_REMOTE="${LINUX_REMOTE:-https://github.com/mithro/linux-litex.git}"
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
		git clone $LINUX_CLONE_FROM linux
	)
	fi

	# Change into the dir
	cd $LINUX_SRC

	# Add the remote if it doesn't exist
	LINUX_REMOTE_NAME=$(git remote -v | grep fetch | grep "$LINUX_REMOTE_BIT" | sed -e's/\t.*$//')
	if [ x"$LINUX_REMOTE_NAME" = x ]; then
		git remote add $REMOTE_NAME https://github.com/enjoy-digital/litex.git
		LINUX_REMOTE_NAME=$REMOTE_NAME
	fi

	# Get any new data
	git fetch $LINUX_REMOTE_NAME

	# Checkout or1k-linux branch it not already on it
	if [ "$(git rev-parse --abbrev-ref HEAD)" != "$LINUX_BRANCH" ]; then
		git checkout $LINUX_BRANCH || \
			git checkout "$LINUX_REMOTE_NAME/$LINUX_BRANCH" -b $LINUX_BRANCH
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
		if [ ! -e openrisc-rootfs.cpio ]; then
			wget "https://drive.google.com/a/mithis.com/uc?authuser=0&id=0B5VlNZ_Rvdw6d21LWXdHQlZuOVU&export=download" -O openrisc-rootfs.cpio
		fi
		if [ ! -e openrisc-rootfs.cpio.gz ]; then
			gzip openrisc-rootfs.cpio
		fi
	)
	make O="$TARGET_LINUX_BUILD_DIR" litex_defconfig
	make O="$TARGET_LINUX_BUILD_DIR" -j$JOBS
	ls -l $TARGET_LINUX_BUILD_DIR/arch/openrisc/boot/vmlinux.bin
	ln -s $TARGET_LINUX_BUILD_DIR/arch/openrisc/boot/vmlinux.bin $TOP_DIR/$FIRMWARE_FILEBASE.bin
)
