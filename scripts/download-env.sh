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

if [ $SOURCED = 1 ]; then
	echo "You must run this script, rather then try to source it."
	echo "$SETUP_SRC"
	return
fi

if [ ! -z "$SETTINGS_FILE" -o ! -z "$XILINX" ]; then
	echo "You appear to have sourced the Xilinx ISE settings, these are incompatible with setting up."
	echo "Please exit this terminal and run again from a clean shell."
	exit 1
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
	if [ ! -d "$XILINX_DIR" -o ! -d "$XILINX_DIR/opt" ]; then
		(
			cd $BUILD_DIR
			mkdir -p Xilinx
			cd Xilinx

			wget -q http://xilinx.timvideos.us/index.txt -O xilinx-details.txt
			XILINX_TAR_INFO=$(cat xilinx-details.txt | grep tar.bz2.gpg | tail -n 1)
			XILINX_TAR_FILE=$(echo $XILINX_TAR_INFO | sed -e's/[^ ]* //' -e's/.gpg$//')
			XILINX_TAR_MD5=$(echo $XILINX_TAR_INFO | sed -e's/ .*//')

			# This setup was taken from https://github.com/m-labs/artiq/blob/master/.travis/get-xilinx.sh
			wget --no-verbose -c http://xilinx.timvideos.us/${XILINX_TAR_FILE}.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 ${XILINX_TAR_FILE}.gpg
			tar -xjf $XILINX_TAR_FILE

			# Remove the tar file to free up space.
			rm ${XILINX_TAR_FILE}*

			# FIXME: Hacks to try and make Vivado work.
			mkdir -p $XILINX_DIR/opt/Xilinx/Vivado/2017.3/scripts/rt/data/svlog/sdbs
			mkdir -p $XILINX_DIR/opt/Xilinx/Vivado/2017.3/tps/lnx64/jre

			# Make ISE stop complaining about missing wbtc binary
			mkdir -p $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64
			ln -s /bin/true $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/wbtc

			# Relocate ISE from /opt to $XILINX_DIR
			for i in $(grep -l -Rsn "/opt/Xilinx" $XILINX_DIR/opt)
			do
				sed -i -e "s!/opt/Xilinx!$XILINX_DIR/opt/Xilinx!g" $i
			done
			wget --no-verbose http://xilinx.timvideos.us/Xilinx.lic.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 Xilinx.lic.gpg

			#git clone https://github.com/mithro/impersonate_macaddress
			#cd impersonate_macaddress
			#make
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

function fix_conda {
	for py in $(find $CONDA_DIR -name envs_manager.py); do
		START_SUM=$(sha256sum $py | sed -e's/ .*//')
		sed -i -e"s^expand(join('~', '.conda', 'environments.txt'))^join('$CONDA_DIR', 'environments.txt')^" $py
		END_SUM=$(sha256sum $py | sed -e's/ .*//')
		if [ $START_SUM != $END_SUM ]; then
			sed -i -e"s/$START_SUM/$END_SUM/" $(find $CONDA_DIR -name paths.json)
		fi
	done
}

echo ""
echo "Initializing environment"
echo "---------------------------------"
# Install and setup conda for downloading packages
export PATH=$CONDA_DIR/bin:$PATH:/sbin
(
	echo
	echo "Installing conda (self contained Python environment with binary package support)"
	if [[ ! -e $CONDA_DIR/bin/conda ]]; then
		cd $BUILD_DIR
		# FIXME: Get the miniconda people to add a "self check" mode
		wget --no-verbose --continue https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
		chmod a+x Miniconda3-latest-Linux-x86_64.sh
		# -p to specify the install location
		# -b to enable batch mode (no prompts)
		# -f to not return an error if the location specified by -p already exists
		./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b -f
		fix_conda
		conda config --system --set always_yes yes
		conda config --system --set changeps1 no
		conda config --system --add envs_dirs $CONDA_DIR/envs
		conda config --system --add pkgs_dirs $CONDA_DIR/pkgs
		conda update -q conda
	fi
	fix_conda
	conda config --system --add channels timvideos
	conda info
)

eval $(cd $TOP_DIR; export HDMI2USB_ENV=1; make env || return 1) || exit 1
(
	cd $TOP_DIR
	export HDMI2USB_ENV=1
	make info || return 1
	echo
) || exit 1

# Check the Python version
echo
echo "Installing python3.5"
conda install -y $CONDA_FLAGS python=3.5
fix_conda
check_version python 3.5
echo "python ==3.5.4" > $CONDA_DIR/conda-meta/pinned # Make sure it stays at version 3.5

echo ""
echo "Installing binaries into environment"
echo "---------------------------------"

# fxload
if [ "$PLATFORM" == "opsis" -o "$PLATFORM" == "atlys" ]; then
	echo
	echo "Installing fxload (tool for Cypress FX2)"
	# conda install fxload
	check_exists fxload
fi

# FIXME: Remove this once @jimmo has finished his new firmware
# MimasV2Config.py
if [ "$PLATFORM" == "mimasv2" ]; then
	MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py
	echo
	echo "Installing MimasV2Config.py (mimasv2 flashing tool)"
	if [ ! -e $MIMASV2CONFIG ]; then
		wget https://raw.githubusercontent.com/numato/samplecode/master/FPGA/MimasV2/tools/configuration/python/MimasV2Config.py -O $MIMASV2CONFIG
		chmod a+x $MIMASV2CONFIG
	fi
	check_exists MimasV2Config.py
fi

# elbertconfig.py
if [ "$PLATFORM" == "elbertv2" ]; then
	ELBERTCONFIG=$BUILD_DIR/conda/bin/elbertconfig.py
	echo
	echo "Installing elbertconfig.py (Elbert flashing tool)"
	if [ ! -e $ELBERTCONFIG ]; then
		wget https://raw.githubusercontent.com/numato/samplecode/master/FPGA/ElbertV2/tools/configuration/python/elbertconfig.py -O $ELBERTCONFIG
		chmod a+x $ELBERTCONFIG
	fi
	check_exists elbertconfig.py
fi

# flterm
echo
echo "Installing flterm (serial terminal tool)"
conda install -y $CONDA_FLAGS flterm
check_exists flterm

# binutils for the target
echo
echo "Installing binutils for ${CPU} (assembler, linker, and other tools)"
conda install -y $CONDA_FLAGS binutils-${CPU}-elf=$BINUTILS_VERSION
check_version ${CPU}-elf-ld $BINUTILS_VERSION

# gcc for the target
echo
echo "Installing gcc for ${CPU} ('bare metal' C cross compiler)"
conda install -y $CONDA_FLAGS gcc-${CPU}-elf-nostdc=$GCC_VERSION
check_version ${CPU}-elf-gcc $GCC_VERSION

# gdb for the target
#echo
#echo "Installing gdb for ${CPU} (debugger)"
#conda install -y $CONDA_FLAGS gdb-${CPU}-elf=$GDB_VERSION
#check_version ${CPU}-elf-gdb $GDB_VERSION

# openocd for programming via Cypress FX2
echo
echo "Installing openocd (jtag tool for programming and debug)"
conda install -y $CONDA_FLAGS openocd=$OPENOCD_VERSION
check_version openocd $OPENOCD_VERSION

echo ""
echo "Installing Python modules into environment"
echo "---------------------------------------"
# pyserial for communicating via uarts
echo
echo "Installing pyserial (python module)"
conda install -y $CONDA_FLAGS pyserial
check_import serial

# ipython for interactive debugging
echo
echo "Installing ipython (python module)"
conda install -y $CONDA_FLAGS ipython
check_import IPython

# progressbar2 for progress bars
echo
echo "Installing progressbar2 (python module)"
pip install --upgrade progressbar2
check_import progressbar

# colorama for progress bars
echo
echo "Installing colorama (python module)"
pip install --upgrade colorama
check_import colorama

# hexfile for embedding the Cypress FX2 firmware.
echo
echo "Installing hexfile (python module)"
pip install --upgrade git+https://github.com/mithro/hexfile.git
check_import_version hexfile $HEXFILE_VERSION

# Tool for changing the mode (JTAG/Serial/etc) of HDMI2USB boards
echo
echo "Installing HDMI2USB-mode-switch (flashing and config tool)"
pip install --upgrade git+https://github.com/timvideos/HDMI2USB-mode-switch.git
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
	git status
)

# lite
for LITE in $LITE_REPOS; do
	LITE_DIR=$THIRD_DIR/$LITE
	(
		echo
		cd $LITE_DIR
		echo "Installing $LITE from $LITE_DIR (local python module)"
		python setup.py develop
	)
	check_import $LITE
done

echo "-----------------------"
echo ""
echo "Completed.  To load environment:"
echo "source $SETUP_DIR/enter-env.sh"
