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

if [ $SOURCED = 1 ]; then
	echo "You must run this script, rather then try to source it."
	echo "$SETUP_SRC"
	return
fi

if [ ! -z "$HDMI2USB_ENV" ]; then
	echo "You appear to have sourced the HDMI2USB settings, these are incompatible with setting up."
	echo "Please exit this terminal and run again from a clean shell."
	exit 1
fi

if [ ! -z "$SETTINGS_FILE" -o ! -z "$XILINX" ]; then
	echo "You appear to have sourced the Xilinx ISE settings, these are incompatible with setting up."
	echo "Please exit this terminal and run again from a clean shell."
	exit 1
fi

set -e

. $SETUP_DIR/settings.sh

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"
echo "     3rd party directory is: $THIRD_DIR"

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
	mkdir -p $BUILD_DIR
fi

# FIXME: Move this to a separate script!
# Cutback Xilinx ISE for CI
# --------
# Save the passphrase to a file so we don't echo it in the logs
if [ ! -z "$XILINX_PASSPHRASE" ]; then
	XILINX_PASSPHRASE_FILE=$(tempfile -s .passphrase | mktemp --suffix=.passphrase)
	trap "rm -f -- '$XILINX_PASSPHRASE_FILE'" EXIT
	echo $XILINX_PASSPHRASE >> $XILINX_PASSPHRASE_FILE

	# Need gpg to do the unencryption
	XILINX_DIR=$BUILD_DIR/Xilinx
	if [ ! -d "$XILINX_DIR" ]; then
		(
			cd $BUILD_DIR
			mkdir Xilinx
			cd Xilinx

			wget -q http://xilinx.timvideos.us/index.txt -O xilinx-details.txt
			XILINX_TAR_INFO=$(cat xilinx-details.txt | grep tar.bz2.gpg | tail -n 1)
			XILINX_TAR_FILE=$(echo $XILINX_TAR_INFO | sed -e's/[^ ]* //' -e's/.gpg$//')
			XILINX_TAR_MD5=$(echo $XILINX_TAR_INFO | sed -e's/ .*//')

			# This setup was taken from https://github.com/m-labs/artiq/blob/master/.travis/get-xilinx.sh
			wget -c http://xilinx.timvideos.us/${XILINX_TAR_FILE}.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 ${XILINX_TAR_FILE}.gpg
			tar -xjf $XILINX_TAR_FILE

			# Relocate ISE from /opt to $XILINX_DIR
			for i in $(grep -Rsn "/opt/Xilinx" $XILINX_DIR/opt | cut -d':' -f1)
			do
				sed -i -e "s!/opt/Xilinx!$XILINX_DIR/opt/Xilinx!g" $i
			done

			wget -c http://xilinx.timvideos.us/Xilinx.lic.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 Xilinx.lic.gpg

			git clone https://github.com/mithro/impersonate_macaddress
			cd impersonate_macaddress
			make
		)
	fi
	export MISOC_EXTRA_CMDLINE="-Ob toolchain_path $XILINX_DIR/opt/Xilinx/"
	# Reserved MAC address from documentation block, see
	# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
	export XILINXD_LICENSE_FILE=$XILINX_DIR
	export MACADDR=90:10:00:00:00:01
	#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
	#ls -l $LD_PRELOAD

	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
elif [ -z "$XILINX_DIR" ]; then
	XILINX_DIR=/
fi
echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"

function check_exists {
	TOOL=$1
	if which $TOOL 2>&1; then
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

# Install and setup conda for downloading packages
echo ""
echo "Install modules from conda"
echo "---------------------------"
export PATH=$CONDA_DIR/bin:$PATH
(
	if [ ! -d $CONDA_DIR ]; then
		cd $BUILD_DIR
		wget -c https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
		chmod a+x Miniconda3-latest-Linux-x86_64.sh
	        ./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b
		conda config --set always_yes yes --set changeps1 no
		conda update -q conda
	fi
	conda config --add channels timvideos
)

# fxload
#(
#	conda install fxload
#)
check_exists fxload

# MimasV2Config.py
MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py
if [ ! -e $MIMASV2CONFIG ]; then
	wget https://raw.githubusercontent.com/numato/samplecode/master/FPGA/MimasV2/tools/configuration/python/MimasV2Config.py -O $MIMASV2CONFIG
	chmod a+x $MIMASV2CONFIG
fi
check_exists MimasV2Config.py

# flterm
(
	conda install flterm
)
check_exists flterm

# binutils for the target
(
	conda install binutils-lm32-elf=$BINUTILS_VERSION
)
check_version lm32-elf-ld $BINUTILS_VERSION

# gcc+binutils for the target
(
	conda install gcc-lm32-elf=$GCC_VERSION
)
check_version lm32-elf-gcc $GCC_VERSION

# openocd for programming via Cypress FX2
(
	conda install openocd
)
check_version openocd 0.10.0-dev

# pyserial for communicating via uarts
(
	conda install pyserial
)
check_import serial

# ipython for interactive debugging
(
	conda install ipython
)
check_import IPython

# progressbar2 for progress bars
(
	pip install --upgrade progressbar2
)
check_import progressbar

# colorama for progress bars
(
	pip install --upgrade colorama
)
check_import colorama

# hexfile for embedding the Cypress FX2 firmware.
(
	pip install --upgrade git+https://github.com/mithro/hexfile.git
)
check_import_version hexfile $HEXFILE_VERSION

# Tool for changing the mode (JTAG/Serial/etc) of HDMI2USB boards
(
	pip install --upgrade git+https://github.com/timvideos/HDMI2USB-mode-switch.git
)
check_import_version hdmi2usb.modeswitch $HDMI2USB_MODESWITCH_VERSION

# git submodules
echo ""
echo "Updating git submodules"
echo "-----------------------"
(
	cd $TOP_DIR
	git submodule update --recursive --init
	git submodule foreach \
		git submodule update --recursive --init
)

# lite
for LITE in $LITE_REPOS; do
	LITE_DIR=$THIRD_DIR/$LITE
	(
		cd $LITE_DIR
		python setup.py develop
	)
	check_import $LITE
done

echo "-----------------------"
echo ""
echo "Completed.  To load environment:"
echo "source $SETUP_DIR/enter-env.sh"
