#!/bin/bash

set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[@]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build
PREBUILT_DIR=$BUILD_DIR/prebuilt

if [ ! -e $BUILD_DIR ]; then
	echo "$BUILD_DIR does not exist so it looks like the prerequisite tools may not be available"
	echo "They can be installed by running scripts/get-env-root.sh and scripts/get-env.sh"
	exit 1
fi

CURRENT_GIT_REVISION=$(git symbolic-ref --short HEAD)/$(git describe)

: ${BOARD:="atlys"}
: ${TARGET:="hdmi2usb"}
: ${PREBUILT_RELEASE:=$CURRENT_GIT_REVISION}
: ${PREBUILT_REPO:="timvideos/HDMI2USB-firmware-prebuilt"}


if [ "$TARGET" = "hdmi2usb" ]; then
	GATEWARE="${BOARD}_hdmi2usb-hdmi2usbsoc-${BOARD}.bit"
elif  [ "$TARGET" = "base" ]; then
	GATEWARE="${BOARD}_base-basesoc-${BOARD}.bit"
fi

FIRMWARE="hdmi2usb.hex"

GATEWARE_DIR="$TOP_DIR/third_party/misoc/build"
FIRMWARE_DIR="$TOP_DIR/firmware/fx2"

# Check nothing exists before we start
if [ -e $GATEWARE_DIR/$GATEWARE -o -e $FIRMWARE_DIR/$FIRMWARE ]; then
	echo ""
	echo "It looks like a build has been run before"
	echo "Run make clean then try again"
	echo ""
	exit 1
elif [ -e $PREBUILT_DIR ]; then
	echo ""
	echo "It looks like a download has been run before"
	echo "Run make clean then try again"
	echo ""
	exit 1
fi

BASE_URL="https://github.com/${PREBUILT_REPO}/raw/master/archive/${PREBUILT_RELEASE}/${BOARD}/${TARGET}"

SHA256SUM_FILE="sha256sum.txt"

(
	mkdir $PREBUILT_DIR
	cd $PREBUILT_DIR
	echo ""
	echo "BOARD=$BOARD TARGET=$TARGET PREBUILT_RELEASE=$PREBUILT_RELEASE"
	echo "Downloading files from https://github.com/${PREBUILT_REPO} ..."
	echo ""
	wget -nv ${BASE_URL}/${SHA256SUM_FILE}
	FILES=$(cat ${SHA256SUM_FILE}| awk -F' ' '{printf "%s ", $2}')
	for f in $FILES; do
		wget -nv ${BASE_URL}/${f}
	done
	echo ""
	echo "Checking sha256sum of downloaded files ..."
	sha256sum -c $SHA256SUM_FILE
	# Script will exit if sums don't match after sha256sum command above
	echo ""
	echo "Copying files to correct locations ..."	
	mkdir -p $GATEWARE_DIR
	cp $GATEWARE $GATEWARE_DIR
	# Not all builds generate FX2 firmware
	if [ -e $FIRMWARE ]; then
		mkdir -p $FIRMWARE_DIR
		cp $FIRMWARE $FIRMWARE_DIR
	fi
	echo ""
	echo "Done"
	echo ""
)
