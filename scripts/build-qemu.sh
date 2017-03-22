#!/bin/bash

set -x
set -e

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

if [ ! -d build/qemu ]; then
	git clone https://github.com/mithro/qemu-litex.git
fi

TARGET_BUILD_DIR=$(realpath build)/${PLATFORM}_${TARGET}_${CPU}/

if [ ! -d $TARET_BUILD_DIR/software/include/generated ]; then
	make firmware
fi

QEMU_BUILD_DIR=$TARGET_BUILD_DIR/qemu
if [ ! -f "$QEMU_BUILD_DIR/Makefile" ]; then
	mkdir -p $QEMU_BUILD_DIR
	(
		cd $QEMU_BUILD_DIR
		../../qemu/configure \
			--target-list=$CPU-softmmu \
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
cd $QEMU_BUILD_DIR
make -j128
cd $OLD_DIR

/usr/bin/env python mkimage.py --output-file=qemu.bin --override-gateware=none

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

$QEMU_BUILD_DIR/$CPU-softmmu/qemu-system-$CPU \
	-M litex \
	-nographic -nodefaults \
	-monitor pty \
	-serial stdio \
	-bios $TARGET_BUILD_DIR/software/bios/bios.bin \
	-kernel $TARGET_BUILD_DIR/qemu.bin \
	$EXTRA_ARGS


