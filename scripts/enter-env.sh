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

. $SETUP_DIR/settings.sh

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"
echo "     3rd party directory is: $THIRD_DIR"

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
	echo "Build directory not found!"
	return 1
fi

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
export PATH=$CONDA_DIR/bin:$PATH:/sbin

eval $(cd $TOP_DIR; export HDMI2USB_ENV=1; make env || return 1) || return 1
(
	cd $TOP_DIR
	export HDMI2USB_ENV=1
	make info || return 1
	echo
) || return 1


# Check the Python version




check_version python 3.6 || return 1

# FPGA toolchain
################################################
echo ""
echo "Checking FPGA toolchain"
echo "---------------------------------------"
PLATFORM_TOOLCHAIN=$(grep 'class Platform' $TOP_DIR/platforms/$PLATFORM.py | sed -e's/class Platform(//' -e's/Platform)://')
echo ""
echo "Platform Toolchain: $PLATFORM_TOOLCHAIN"
case $PLATFORM_TOOLCHAIN in
	Xilinx)
		if [ -z "$LIKELY_XILINX_LICENSE_DIR" ]; then
			LIKELY_XILINX_LICENSE_DIR="$HOME/.Xilinx"
		fi

		XILINX_SETTINGS_ISE='/opt/Xilinx/*/ISE_DS/settings64.sh'
		XILINX_SETTINGS_VIVADO='/opt/Xilinx/Vivado/*/settings64.sh'

		if [ -z "$XILINX_DIR" ]; then
			LOCAL_XILINX_DIR=$BUILD_DIR/Xilinx
			if [ -d "$LOCAL_XILINX_DIR/opt/Xilinx/" ]; then
				# Reserved MAC address from documentation block, see
				# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
				export LIKELY_XILINX_LICENSE_DIR=$LOCAL_XILINX_DIR
				export MACADDR=90:10:00:00:00:01
				#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
				#ls -l $LD_PRELOAD
				export XILINX_DIR=$LOCAL_XILINX_DIR
				export XILINX_LOCAL_USER_DATA=no
			fi
		fi
		if [ -z "$LIKELY_XILINX_LICENSE_DIR" ]; then
			LIKELY_XILINX_LICENSE_DIR="$HOME/.Xilinx"
		fi

		# Find Xilinx toolchain versions...
		shopt -s nullglob
		XILINX_SETTINGS_ISE=($XILINX_DIR/$XILINX_SETTINGS_ISE)
		XILINX_SETTINGS_VIVADO=($XILINX_DIR/$XILINX_SETTINGS_VIVADO)
		shopt -u nullglob

		# Tell user what we found...
		echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"
		if [ ${#XILINX_SETTINGS_ISE[@]} -gt 0 ]; then
			echo -n "                             - Xilinx ISE toolchain found!"
			if [ ${#XILINX_SETTINGS_ISE[@]} -gt 1 ]; then
				echo -n " (${#XILINX_SETTINGS_ISE[@]} versions)"
			fi
			echo ""
			export HAVE_XILINX_ISE=1
		else
			echo "                             - *No* Xilinx ISE toolchain found"
			export HAVE_XILINX_ISE=0
		fi
		if [ ${#XILINX_SETTINGS_VIVADO[@]} -gt 0 ]; then
			echo -n "                             - Xilinx Vivado toolchain found!"
			if [ ${#XILINX_SETTINGS_VIVADO[@]} -gt 1 ]; then
				echo -n " (${#XILINX_SETTINGS_VIVADO[@]} versions)"
			fi
			echo ""
			export HAVE_XILINX_VIVADO=1
		else
			echo "                             - *No* Xilinx Vivado toolchain found!"
			export HAVE_XILINX_VIVADO=0
		fi
		if [ $HAVE_XILINX_ISE -eq 1 -o $HAVE_XILINX_VIVADO -eq 1 ]; then
			export HAVE_XILINX_TOOLCHAIN=1
			export HAVE_FPGA_TOOLCHAIN=1
		else
			echo "                             - *No* Xilinx toolchain found!"
			export HAVE_XILINX_TOOLCHAIN=0
			export HAVE_FPGA_TOOLCHAIN=0
		fi
		if [ $HAVE_XILINX_TOOLCHAIN -eq 1 ]; then
			export MISOC_EXTRA_CMDLINE="-Ob toolchain_path $XILINX_DIR/opt/Xilinx/"
		fi

		# Detect a likely lack of license early, but just warn if it's missing
		# just in case they've set it up elsewhere.
		if [ ! -e $LIKELY_XILINX_LICENSE_DIR/Xilinx.lic ]; then
			echo "(WARNING) Please ensure you have installed Xilinx and have a license."
			echo "(WARNING) Copy your Xilinx license to Xilinx.lic in $LIKELY_XILINX_LICENSE_DIR to suppress this warning."
		else
			echo "          Xilinx license in: $LIKELY_XILINX_LICENSE_DIR"
			export XILINXD_LICENSE_FILE=$LIKELY_XILINX_LICENSE_DIR
		fi
		;;
	Lattice)
		export HAVE_FPGA_TOOLCHAIN=1
		# yosys



		check_exists yosys || return 1

		# nextpnr



		check_exists nextpnr-ice40 || return 1
		;;
	Sim)
		export HAVE_FPGA_TOOLCHAIN=1
		# verilator



		check_exists verilator || return 1
		;;
	*)
		;;
esac


# FPGA Programming tools
################################################
echo ""
echo "Checking programming tools in environment"
echo "-----------------------------------------"

# tinyfpga boards
if [ "$PLATFORM" = "tinyfpga_b2" ]; then



	check_exists tinyfpgab || return 1
fi
if [ "$PLATFORM" = "tinyfpga_bx" ]; then



	check_exists tinyprog || return 1
fi

# fxload
if [ "$PLATFORM" = "opsis" -o "$PLATFORM" = "atlys" ]; then



	check_exists fxload || return 1
fi

# FIXME: Remove this once @jimmo has finished his new firmware
# MimasV2Config.py
if [ "$PLATFORM" = "mimasv2" ]; then
	MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py






	check_exists MimasV2Config.py || return 1
fi

# flterm



check_exists flterm || return 1

# openocd for programming via Cypress FX2



check_version openocd $OPENOCD_VERSION || return 1


# C compiler toolchain
################################################
echo ""
echo "Checking C compiler toolchain"
echo "---------------------------------------"
if [ "$CPU" = "lm32" -o "$CPU" = "or1k" ]; then
	CPU_ARCH=$CPU
elif [ "$CPU" = "vexriscv" -o "$CPU" = "picorv32" ]; then
	CPU_ARCH=riscv32
fi

# binutils for the target



check_version ${CPU_ARCH}-elf-ld $BINUTILS_VERSION || return 1

# gcc for the target



check_version ${CPU_ARCH}-elf-gcc $GCC_VERSION || return 1

# gdb for the target
#
#
#
#check_version ${CPU_ARCH}-elf-gdb $GDB_VERSION


# Python modules
################################################
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

# git commands
echo ""
echo "Checking git submodules"
echo "-----------------------"
(
	cd $TOP_DIR



	git submodule status --recursive
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
