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

# Xilinx ISE

# --------
# Save the passphrase to a file so we don't echo it in the logs
XILINX_PASSPHRASE_FILE=$(tempfile)
trap "rm -f -- '$XILINX_PASSPHRASE_FILE'" EXIT
if [ ! -z "$XILINX_PASSPHRASE" ]; then
	echo $XILINX_PASSPHRASE >> $XILINX_PASSPHRASE_FILE
else
	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
fi
# --------

if [ -f $XILINX_PASSPHRASE_FILE ]; then
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
	export MISOC_EXTRA_CMDLINE="-Ob ise_path $XILINX_DIR/opt/Xilinx/"
	# Reserved MAC address from documentation block, see
	# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
	export XILINXD_LICENSE_FILE=$XILINX_DIR
	export MACADDR=90:10:00:00:00:01
	#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
	#ls -l $LD_PRELOAD

	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
else
	XILINX_DIR=/
fi
echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"

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

# sdcc for compiling Cypress FX2 firmware
(
	conda install sdcc=$SDCC_VERSION
)
check_version sdcc $SDCC_VERSION

# openocd for programming via Cypress FX2
(
	conda install openocd
)
check_version openocd 0.10.0-dev

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

# migen
MIGEN_DIR=$THIRD_DIR/migen
(
	cd $MIGEN_DIR
	cd vpi
	#make all
	#sudo make install
)
export PYTHONPATH=$MIGEN_DIR:$PYTHONPATH
check_import migen

# misoc
MISOC_DIR=$THIRD_DIR/misoc
(
	cd $MISOC_DIR
	cd tools
	make
)
export PYTHONPATH=$MISOC_DIR:$PYTHONPATH
$MISOC_DIR/tools/flterm --help 2> /dev/null
check_import misoclib

# liteeth
LITEETH_DIR=$THIRD_DIR/liteeth
(
	cd $LITEETH_DIR
	true
)
export PYTHONPATH=$LITEETH_DIR:$PYTHONPATH
check_import liteeth

# liteusb
LITEUSB_DIR=$THIRD_DIR/liteusb
(
	cd $LITEUSB_DIR
	true
)
export PYTHONPATH=$LITEUSB_DIR:$PYTHONPATH
check_import liteusb

echo "-----------------------"
echo ""
echo "Completed.  To load environment:"
echo "source HDMI2USB-misoc-firmware/scripts/setup-env.sh"
