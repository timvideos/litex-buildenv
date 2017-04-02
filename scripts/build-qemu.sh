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

if [ -z "$PLATFORM" ]; then
	echo "Please set PLATFORM"
	exit 1
fi
if [ -z "$TARGET" ]; then
	echo "Please set TARGET"
	exit 1
fi
if [ -z "$CPU" ]; then
	echo "Please set CPU"
	exit 1
fi

set -x
set -e

QEMU_SRC_DIR=$TOP_DIR/third_party/qemu-litex
if [ ! -d "$QEMU_SRC_DIR" ]; then
	(
		cd $(dirname $QEMU_SRC_DIR)
		git clone https://github.com/timvideos/qemu-litex.git
		cd $QEMU_SRC_DIR
		git submodule update --init dtc
	)
fi

TARGET_BUILD_DIR=$(realpath build)/${PLATFORM}_${TARGET}_${CPU}/
TARGET_QEMU_BUILD_DIR=$TARGET_BUILD_DIR/qemu

case $CPU in
	lm32)
		QEMU_CPU=lm32
		;;
	or1k)
		QEMU_CPU=or32
		;;
	*)
		echo "CPU $CPU isn't supported at the moment."
		exit 1
		;;
esac
QEMU_ARCH=$QEMU_CPU-softmmu

if [ ! -d $TARGET_BUILD_DIR/software/include/generated ]; then
	make firmware
fi

if [ ! -f "$TARGET_QEMU_BUILD_DIR/Makefile" ]; then
	mkdir -p $TARGET_QEMU_BUILD_DIR
	(
		cd $TARGET_QEMU_BUILD_DIR
		$QEMU_SRC_DIR/configure \
			--target-list=$QEMU_ARCH \
			--python=/usr/bin/python2 \
			--enable-fdt \
			--disable-kvm \
			--disable-xen \
			--enable-debug \
			--enable-debug-info

		ln -s $(realpath $PWD/../software/include/generated) generated
	)
fi


OLD_DIR=$PWD
cd $TARGET_QEMU_BUILD_DIR
make -j8
cd $OLD_DIR

/usr/bin/env python mkimage.py --output-file=qemu.bin --override-gateware=none --force-image-size=true
$TARGET_QEMU_BUILD_DIR/qemu-img convert -f raw $TARGET_BUILD_DIR/qemu.bin -O qcow2 -S 16M $TARGET_BUILD_DIR/qemu.qcow2

HAS_LITEETH=$(grep -q ETHMAC_BASE $TARGET_BUILD_DIR/software/include/generated/csr.h && echo 1 || echo 0)

if [ $HAS_LITEETH -eq 1 ]; then
	if [ ! -e /dev/net/tap0 ]; then
	        sudo true
		echo "Need to bring up a tun device."
		IPRANGE=192.168.100
	        sudo openvpn --mktun --dev tap0
	        sudo ifconfig tap0 $IPRANGE.100 up
	        sudo mknod /dev/net/tap0 c 10 200
	        sudo chown $(whoami) /dev/net/tap0
		make tftpd_start
	fi
	EXTRA_ARGS="-net nic -net tap,ifname=tap0,script=no,downscript=no"
	make tftp
fi

SPIFLASH_MODEL=$(grep spiflash_model platforms/$PLATFORM.py | sed -e's/[^"]*"//' -e's/".*$//')
echo $SPIFLASH_MODEL

$TARGET_QEMU_BUILD_DIR/$QEMU_ARCH/qemu-system-$QEMU_CPU \
	-M litex \
	-nographic -nodefaults \
	-monitor pty \
	-serial stdio \
	-bios $TARGET_BUILD_DIR/software/bios/bios.bin \
	-drive if=mtd,format=qcow2,file=$TARGET_BUILD_DIR/qemu.qcow2,serial=$SPIFLASH_MODEL \
	$EXTRA_ARGS


