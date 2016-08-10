#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)

if [ $SOURCED = 0 ]; then
	echo "You must source this script, rather then try and run it."
	echo ". $SETUP_SRC"
	exit 1
fi

if [ ! -z $HDMI2USB_ENV ]; then
	echo "Already sourced this file."
	return
fi

if [ ! -z $SETTINGS_FILE ]; then
	echo "You appear to have sourced the Xilinx ISE settings, these are incompatible with building."
	echo "Please exit this terminal and run again from a clean shell."
	return
fi

# Check ixo-usb-jtag *isn't* install
if [ -d /lib/firmware/ixo-usb-jtag/ ]; then
	echo "Please uninstall ixo-usb-jtag package, the require firmware is"
	echo "included in the HDMI2USB modeswitch tool."
	echo
	echo "On Debian/Ubuntu run:"
	echo "  sudo apt-get remove ixo-usb-jtag"
	echo
	return
fi

. $SETUP_DIR/settings.sh

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"
echo "     3rd party directory is: $THIRD_DIR"

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
	echo "Build directory not found!"
	return
fi

# Xilinx ISE
XILINX_DIR=$BUILD_DIR/Xilinx
if [ -f "$XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport" ]; then
	export MISOC_EXTRA_CMDLINE="-Ob ise_path $XILINX_DIR/opt/Xilinx/"
	# Reserved MAC address from documentation block, see
	# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
	export XILINXD_LICENSE_FILE=$XILINX_DIR
	export MACADDR=90:10:00:00:00:01
	#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
	#ls -l $LD_PRELOAD
else
	XILINX_DIR=/
fi
echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"
# FIXME: Remove this when build/migen/mibuild/xilinx/programmer.py:_create_xsvf
# understands the $MISOC_EXTRA_CMDLINE option.
export PATH=$PATH:$XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64

function check_version {
	TOOL=$1
	VERSION=$2
	if $TOOL --version 2>&1 | grep -q $VERSION > /dev/null; then
		echo "$TOOL found at $VERSION"
		return 0
	else
		$TOOL --version
		echo "$TOOL (version $VERSION) *NOT* found"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

function check_import {
	MODULE=$1
	if python3 -c "import $MODULE"; then
		echo "$MODULE found"
		return 0
	else
		echo "$MODULE *NOT* found!"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

function check_import_version {
	MODULE=$1
	EXPECT_VERSION=$2
        ACTUAL_VERSION=$(python3 -c "import $MODULE; print($MODULE.__version__)")
	if echo "$ACTUAL_VERSION" | grep -q $EXPECT_VERSION > /dev/null; then
		echo "$MODULE found at $ACTUAL_VERSION"
		return 0
	else
		echo "$MODULE (version $EXPECT_VERSION) *NOT* found!"
		echo "Please try running the $SETUP_DIR/get-env.sh script again."
		return 1
	fi
}

# Install and setup conda for downloading packages
echo ""
echo "Checking modules from conda"
echo "---------------------------"
export PATH=$CONDA_DIR/bin:$PATH

# binutils for the target



check_version lm32-elf-ld $BINUTILS_VERSION || return 1

# gcc+binutils for the target



check_version lm32-elf-gcc $GCC_VERSION || return 1

# sdcc for compiling Cypress FX2 firmware



check_version sdcc $SDCC_VERSION || return 1

# openocd for programming via Cypress FX2



check_version openocd 0.10.0-dev || return 1

# hexfile for embedding the Cypress FX2 firmware.



check_import_version hexfile $HEXFILE_VERSION

# Tool for changing the mode (JTAG/Serial/etc) of HDMI2USB boards



check_import_version hdmi2usb.modeswitch $HDMI2USB_MODESWITCH_VERSION

# git submodules
echo ""
echo "Checking git submodules"
echo "-----------------------"

# migen
MIGEN_DIR=$THIRD_DIR/migen
export PYTHONPATH=$MIGEN_DIR:$PYTHONPATH
check_import migen || return 1

# misoc
MISOC_DIR=$THIRD_DIR/misoc
export PYTHONPATH=$MISOC_DIR:$PYTHONPATH
$MISOC_DIR/tools/flterm --help 2> /dev/null || (echo "misoc flterm broken" && return 1)
check_import misoclib || return 1

# liteeth
LITEETH_DIR=$THIRD_DIR/liteeth
export PYTHONPATH=$LITEETH_DIR:$PYTHONPATH
check_import liteeth || return 1

# liteusb
LITEUSB_DIR=$THIRD_DIR/liteusb
export PYTHONPATH=$LITEUSB_DIR:$PYTHONPATH
check_import liteusb || return 1

echo "-----------------------"
echo ""

alias python=python3

export HDMI2USB_ENV=1

# Set prompt
ORIG_PS1="$PS1"
hdmi2usb_prompt() {
	P="(H2U B=$BOARD"

	if [ ! -z "$TARGET" ]; then
		P="$P T=$TARGET"
	fi
	if [ ! -z "$PROG" ]; then
		P="$P P=$PROG"
	fi

	BRANCH="$(git symbolic-ref --short HEAD 2> /dev/null)"
	if [ "$BRANCH" != "master" ]; then
		if [ x"$BRANCH" = x ]; then
			BRANCH="???"
		fi
		P="$P R=$BRANCH"
	fi

	PS1="$P) $ORIG_PS1"
}
PROMPT_COMMAND=hdmi2usb_prompt
