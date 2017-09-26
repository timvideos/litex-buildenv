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

QEMU_SRC_DIR=$TOP_DIR/third_party/qemu-litex
if [ ! -d "$QEMU_SRC_DIR" ]; then
	(
		cd $(dirname $QEMU_SRC_DIR)
		git clone https://github.com/timvideos/qemu-litex.git
		cd $QEMU_SRC_DIR
		git submodule update --init dtc
	)
fi

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

/usr/bin/env python mkimage.py $MISOC_EXTRA_CMDLINE $LITEX_EXTRA_CMDLINE --output-file=qemu.bin --override-gateware=none --force-image-size=true $OVERRIDE_FIRMWARE
$TARGET_QEMU_BUILD_DIR/qemu-img convert -f raw $TARGET_BUILD_DIR/qemu.bin -O qcow2 -S 16M $TARGET_BUILD_DIR/qemu.qcow2

# BIOS
if grep -q 'ROM_BASE 0x00000000' $TARGET_BUILD_DIR/software/include/generated/mem.h; then
	echo "Platform has BIOS ROM, adding BIOS"
	EXTRA_ARGS+=("-bios $TARGET_BUILD_DIR/software/bios/bios.bin")
fi

# SPI Flash
if grep -q 'SPIFLASH_BASE' $TARGET_BUILD_DIR/software/include/generated/mem.h; then
	SPIFLASH_MODEL=$(grep spiflash_model platforms/$PLATFORM.py | sed -e's/[^"]*"//' -e's/".*$//')

	echo "Platform has SPI flash - assuming n25q16!"
	EXTRA_ARGS+=("-drive if=mtd,format=qcow2,file=$TARGET_BUILD_DIR/qemu.qcow2,serial=$SPIFLASH_MODEL")
fi

# Ethernet
if grep -q ETHMAC_BASE $TARGET_BUILD_DIR/software/include/generated/csr.h; then
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
	make tftp
	EXTRA_ARGS+=("-net nic -net tap,ifname=tap0,script=no,downscript=no")
fi

SPIFLASH_MODEL=$(grep spiflash_model platforms/$PLATFORM.py | sed -e's/[^"]*"//' -e's/".*$//')
echo $SPIFLASH_MODEL

$TARGET_QEMU_BUILD_DIR/$QEMU_ARCH/qemu-system-$QEMU_CPU \
	-M litex \
	-nographic -nodefaults \
	-monitor pty \
	-serial stdio \
	${EXTRA_ARGS[@]}
