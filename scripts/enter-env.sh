#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC="$(realpath ${BASH_SOURCE[0]})"
SETUP_DIR="$(dirname "${SETUP_SRC}")"
TOP_DIR="$(realpath "${SETUP_DIR}/..")"
LIKELY_XILINX_LICENSE_LOCATION="$HOME/.Xilinx/Xilinx.lic"

if [ $SOURCED = 0 ]; then
	echo "You must source this script, rather than try and run it."
	echo ". $SETUP_SRC"
	exit 1
fi

if [ ! -z "$HDMI2USB_ENV" ]; then
	echo "Already sourced this file."
	return 1
fi

if [ ! -z "$SETTINGS_FILE" -o ! -z "$XILINX" ]; then
	echo "You appear to have sourced the Xilinx ISE settings, these are incompatible with building."
	echo "Please exit this terminal and run again from a clean shell."
	return 1
fi

# Conda does not support ' ' in the path (it bails early).
if echo "${SETUP_DIR}" | grep -q ' '; then
	echo "You appear to have whitespace characters in the path to this script."
	echo "Please move this repository to another path that does not contain whitespace."
	exit 1
fi

# Conda does not support ':' in the path (it fails to install python).
if echo "${SETUP_DIR}" | grep -q ':'; then
	echo "You appear to have ':' characters in the path to this script."
	echo "Please move this repository to another path that does not contain this character."
	exit 1
fi

# Check ixo-usb-jtag *isn't* installed
if [ -e /lib/udev/rules.d/85-ixo-usb-jtag.rules ]; then
	echo "Please uninstall ixo-usb-jtag package from the timvideos PPA, the"
	echo "required firmware is included in the HDMI2USB modeswitch tool."
	echo
	echo "On Debian/Ubuntu run:"
	echo "  sudo apt-get remove ixo-usb-jtag"
	echo
	return 1
fi

if [ -f /etc/udev/rules.d/99-hdmi2usb-permissions.rules -o -f /lib/udev/rules.d/99-hdmi2usb-permissions.rules -o -f /lib/udev/rules.d/60-hdmi2usb-udev.rules -o ! -z "$HDMI2USB_UDEV_IGNORE" ]; then
	true
else
	echo "Please install the HDMI2USB udev rules."
	echo "These are installed by scripts/download-env-root.sh"
	echo
	return 1
fi

# Detect a likely lack of license early, but just warn if it's missing
# just in case they've set it up elsewhere.
license_found=0
if [ ! -e $LIKELY_XILINX_LICENSE_LOCATION ]; then
	echo "(WARNING) Please ensure you have installed Xilinx and have a license."
	echo "(WARNING) Copy your Xilinx license to $LIKELY_XILINX_LICENSE_LOCATION to suppress this warning."
else
	license_found=1
fi

. $SETUP_DIR/settings.sh

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"
echo "     3rd party directory is: $THIRD_DIR"
if [ $license_found == 1 ]; then
	echo "          Xilinx license in: $LIKELY_XILINX_LICENSE_LOCATION"
fi

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
	echo "Build directory not found!"
	return 1
fi

# Xilinx ISE
if [ -z "$XILINX_DIR" ]; then
	LOCAL_XILINX_DIR=$BUILD_DIR/Xilinx
	if [ -f "$LOCAL_XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport" ]; then
		# Reserved MAC address from documentation block, see
		# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
		export XILINXD_LICENSE_FILE=$LOCAL_XILINX_DIR
		export MACADDR=90:10:00:00:00:01
		#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
		#ls -l $LD_PRELOAD
		export XILINX_DIR=$LOCAL_XILINX_DIR
	else
		XILINX_DIR=/
	fi
fi
if [ ! -z "$XILINX_DIR" ]; then
	export MISOC_EXTRA_CMDLINE="-Ob toolchain_path $XILINX_DIR/opt/Xilinx/"
fi
echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"

function check_exists {
	TOOL=$1
	if which $TOOL >/dev/null; then
		echo "$TOOL found at $(which $TOOL)"
		return 0
	else
		echo "$TOOL *NOT* found"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

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
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

echo ""
echo "Checking environment"
echo "---------------------------------"
# Install and setup conda for downloading packages
export PATH=$CONDA_DIR/bin:$PATH

eval $(cd $TOP_DIR; export HDMI2USB_ENV=1; make env || return 1) || return 1
(
	cd $TOP_DIR
	export HDMI2USB_ENV=1
	make info || return 1
	echo
) || return 1

# Check the Python version




check_version python 3.6 || return 1

echo ""
echo "Checking binaries in environment"
echo "---------------------------------"

# fxload
if [ "$PLATFORM" == "opsis" -o "$PLATFORM" == "atlys" ]; then
	# check sbin for fxload as well
	export PATH=$PATH:/sbin

	check_exists fxload || return 1
fi

# FIXME: Remove this once @jimmo has finished his new firmware
# MimasV2Config.py
if [ "$PLATFORM" == "mimasv2" ]; then
	MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py






	check_exists MimasV2Config.py || return 1
fi

# flterm



check_exists flterm || return 1

# binutils for the target



check_version ${CPU}-elf-ld $BINUTILS_VERSION || return 1

# gcc for the target



check_version ${CPU}-elf-gcc $GCC_VERSION || return 1

# gdb for the target
#
#
#
#check_version ${CPU}-elf-gdb $GDB_VERSION

# openocd for programming via Cypress FX2



check_version openocd $OPENOCD_VERSION || return 1

echo ""
echo "Checking Python modules in environment"
echo "---------------------------------------"
# pyserial for communicating via uarts



check_import serial || return 1

# ipython for interactive debugging



check_import IPython || return 1

# progressbar2 for progress bars



check_import progressbar || return 1

# colorama for progress bars



check_import colorama || return 1

# hexfile for embedding the Cypress FX2 firmware.



check_import_version hexfile $HEXFILE_VERSION || return 1

# Tool for changing the mode (JTAG/Serial/etc) of HDMI2USB boards



check_import_version hdmi2usb.modeswitch $HDMI2USB_MODESWITCH_VERSION || return 1

# git submodules
echo ""
echo "Checking git submodules"
echo "-----------------------"
(
	cd $TOP_DIR



	git status
)

# lite
for LITE in $LITE_REPOS; do







	check_import $LITE || return 1
done

echo "-----------------------"
echo ""

alias python=python3

export HDMI2USB_ENV=1

# Set prompt
ORIG_PS1="$PS1"
litex_buildenv_prompt() {
	P="$(cd $TOP_DIR; make prompt)"
	PS1="(LX $P) $ORIG_PS1"
	case "$TERM" in
	xterm*|rxvt*)
		PS1="$PS1\[\033]0;($P) \w\007\]"
		;;
	*)
		;;
	esac
}
PROMPT_COMMAND="litex_buildenv_prompt; ${PROMPT_COMMAND}"
