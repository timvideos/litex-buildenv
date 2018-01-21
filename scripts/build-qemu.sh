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

QEMU_REMOTE="${QEMU_REMOTE:-https://github.com/timvideos/qemu-litex.git}"
QEMU_REMOTE_NAME=timvideos-qemu-litex
QEMU_REMOTE_BIT=$(echo $QEMU_REMOTE | sed -e's-^.*://--' -e's/.git$//')
QEMU_BRANCH=${QEMU_BRANCH:-master}
QEMU_SRC_DIR=$TOP_DIR/third_party/qemu-litex
if [ ! -d "$QEMU_SRC_DIR" ]; then
	(
		cd $(dirname $QEMU_SRC_DIR)
		git clone https://github.com/timvideos/qemu-litex.git
		cd $QEMU_SRC_DIR
		git submodule update --init dtc
	)
else
	(
		cd $QEMU_SRC_DIR

		# Add the remote if it doesn't exist
		CURRENT_QEMU_REMOTE_NAME=$(git remote -v | grep fetch | grep "$QEMU_REMOTE_BIT" | sed -e's/\t.*$//')
		if [ x"$CURRENT_QEMU_REMOTE_NAME" = x ]; then
			git remote add $QEMU_REMOTE_NAME $QEMU_REMOTE
			CURRENT_QEMU_REMOTE_NAME=$QEMU_REMOTE_NAME
		fi

		# Get any new data
		git fetch $CURRENT_QEMU_REMOTE_NAME

		# Checkout master branch it not already on it
		if [ "$(git rev-parse --abbrev-ref HEAD)" != "$QEMU_BRANCH" ]; then
			git checkout $QEMU_BRANCH || \
				git checkout "$CURRENT_QEMU_REMOTE_NAME/$QEMU_BRANCH" -b $QEMU_BRANCH
		fi
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
		CFLAGS="-Wno-error" $QEMU_SRC_DIR/configure \
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
make -j$JOBS
cd $OLD_DIR

# Need the .fbi for mkimage below...
if [ ! -d $FIRMWARE_FILEBASE.fbi ]; then
	make $FIRMWARE_FILEBASE.fbi
fi

QEMU_IMAGE_FILE=$IMAGE_FILE.4qemu
/usr/bin/env python mkimage.py $MISOC_EXTRA_CMDLINE $LITEX_EXTRA_CMDLINE $MAKE_LITEX_EXTRA_CMDLINE --output-file=$QEMU_IMAGE_FILE --override-gateware=none --force-image-size=true $OVERRIDE_FIRMWARE
$TARGET_QEMU_BUILD_DIR/qemu-img convert -f raw $QEMU_IMAGE_FILE -O qcow2 -S 16M $TARGET_BUILD_DIR/qemu.qcow2

# BIOS
if grep -q 'ROM_BASE 0x00000000' $TARGET_BUILD_DIR/software/include/generated/mem.h; then
	echo "Platform has BIOS ROM, adding BIOS"
	EXTRA_ARGS+=("-bios $BIOS_FILE")
fi

# SPI Flash
if grep -q 'SPIFLASH_BASE' $TARGET_BUILD_DIR/software/include/generated/mem.h; then
	SPIFLASH_MODEL=$(grep spiflash_model platforms/$PLATFORM.py | sed -e's/[^"]*"//' -e's/".*$//')
	if [ -z "$SPIFLASH_MODEL" ]; then
		echo "Platform has unknown SPI flash - assuming m25p16!"
		SPIFLASH_MODEL=m25p16
	fi
	EXTRA_ARGS+=("-drive if=mtd,format=qcow2,file=$TARGET_BUILD_DIR/qemu.qcow2,serial=$SPIFLASH_MODEL")
fi

# Ethernet
if grep -q ETHMAC_BASE $TARGET_BUILD_DIR/software/include/generated/csr.h; then
	QEMU_NETWORK=${QEMU_NETWORK:-tap}
	case $QEMU_NETWORK in
	tap)
		echo "Using tun device for QEmu networking, (may need sudo)..."
		# Make the tap0 dev node exists
		if [ ! -e /dev/net/tap0 ]; then
			sudo true
			sudo mknod /dev/net/tap0 c 10 200
			sudo chown $(whoami) /dev/net/tap0
		fi

		# Check that the tap0 network interface exists
		if [ ! -e /sys/class/net/tap0 ]; then
			sudo true
			if sudo which openvpn > /dev/null; then
				sudo openvpn --mktun --dev tap0 --user $(whoami)
			elif sudo which tunctl > /dev/null; then
				sudo tunctl -t tap0 -u $(whoami)
			else
				echo "Unable to find tool to create tap0 device!"
				exit 1
			fi
		fi

		# Check the tap0 device if configure and up
		if sudo which ifconfig > /dev/null; then
			if ! ifconfig tap0 | grep -q "UP" || ! ifconfig tap0 | grep -q "$TFTP_IPRANGE.100"; then
				sudo true
				sudo ifconfig tap0 $TFTP_IPRANGE.100 netmask 255.255.255.0 up
			fi
		elif sudo which ip > /dev/null; then
			if ! ip addr show tap0 | grep -q "UP" || ! ip addr show tap0 | grep -q "$TFTP_IPRANGE.100"; then
				sudo true
				sudo ip addr add $TFTP_IPRANGE.100/24 dev tap0
				sudo ip link set dev tap0 up
			fi
		else
			echo "Unable to find tool to configure tap0 address"
			exit 1
		fi

		# Restart tftpd
		make tftpd_stop
		make tftpd_start

		EXTRA_ARGS+=("-net nic -net tap,ifname=tap0,script=no,downscript=no")
		;;

	user)
		# Make qemu emulate a network device
		EXTRA_ARGS+=("-net nic")
		# Use the userspace network support. QEMU will pretend to be a
		# machine a $TFTP_IPRANGE.100. Any connections to that IP will
		# automatically be forwarded to the real localhost.
		#
		# Connections to real localhost on port 2223, will be
		# forwarded to the expected guest ip ($TFTP_IPRANGE.50) on port
		# 23 (telnet).
		EXTRA_ARGS+=("-net user,net=$TFTP_IPRANGE.0/24,host=$TFTP_IPRANGE.100,dhcpstart=$TFTP_IPRANGE.50,tftp=$TFTPD_DIR,hostfwd=tcp::2223-:23")

		# Make debugging the userspace networking easier, dump all
		# packets to a file.
		# FIXME: Make this optional.
		EXTRA_ARGS+=("-net dump,file=/tmp/data.pcap")
		;;
	none)
		echo "QEmu networking disabled..."
		;;
	*)
		echo "Unknown QEMU_NETWORK mode '$QEMU_NETWORK'"
		;;
	esac

	# Build/copy the image into the TFTP directory.
	make tftp
fi

# Allow gdb connections
EXTRA_ARGS+=("-gdb tcp::10001")

SPIFLASH_MODEL=$(grep spiflash_model platforms/$PLATFORM.py | sed -e's/[^"]*"//' -e's/".*$//')
echo $SPIFLASH_MODEL

$TARGET_QEMU_BUILD_DIR/$QEMU_ARCH/qemu-system-$QEMU_CPU \
	-M litex \
	-nographic -nodefaults \
	-monitor telnet::10000,server,nowait \
	-serial stdio \
	${EXTRA_ARGS[@]}
