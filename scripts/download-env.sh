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
	for CONDA_SITE_PACKAGES in $(realpath $CONDA_DIR/lib/python*/site-packages/); do
		CONDA_COMMON_PATH="$CONDA_SITE_PACKAGES/conda/common/path.py"
		if [ ! -e $CONDA_COMMON_PATH ]; then
			continue
		fi
		if grep -q "def expanduser" $CONDA_COMMON_PATH; then
			echo "In $CONDA_SITE_PACKAGES conda/common/path.py is already patched."
			continue
		fi
		START_SUM=$(sha256sum $CONDA_COMMON_PATH | sed -e's/ .*//')
		(echo -n "In $CONDA_SITE_PACKAGES " && cd $CONDA_SITE_PACKAGES && patch -p1 || exit 1) <<EOF
diff --git a/conda/common/path.py b/conda/common/path.py
index 0228a3d0b..ffb879a39 100644
--- a/conda/common/path.py
+++ b/conda/common/path.py
@@ -42,6 +42,10 @@ def is_path(value):
     return re.match(PATH_MATCH_REGEX, value)
 
 
+def expanduser(path):
+    return expandvars(path.replace('~', '${CONDA_DIR}'))
+
+
 def expand(path):
     # if on_win and PY2:
     #     path = ensure_fs_path_encoding(path)

EOF
		END_SUM=$(sha256sum $CONDA_COMMON_PATH | sed -e's/ .*//')
		if [ $START_SUM != $END_SUM ]; then
			sed -i -e"s/$START_SUM/$END_SUM/" $(find $CONDA_DIR -name paths.json)
		else
			echo "Unable to patch conda path module!"
			return 1
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
		(
			export HOME=$CONDA_DIR
			./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b -f || exit 1
		)
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

echo "python ==${PYTHON_VERSION}" > $CONDA_DIR/conda-meta/pinned # Make sure it stays at given version

# Check the Python version
echo
echo "Installing python${PYTHON_VERSION}"
conda install -y $CONDA_FLAGS python=${PYTHON_VERSION}
fix_conda
check_version python ${PYTHON_VERSION}

# FPGA toolchain
################################################
echo ""
echo "Installing FPGA toolchain"
echo "---------------------------------------"
PLATFORM_TOOLCHAIN=$(grep 'class Platform' $TOP_DIR/platforms/$PLATFORM.py | sed -e's/class Platform(//' -e's/Platform)://')
echo ""
echo "Platform Toolchain: $PLATFORM_TOOLCHAIN"
case $PLATFORM_TOOLCHAIN in
	Xilinx)
		. $TOP_DIR/.travis/download-xilinx.sh

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
		echo
		echo "Installing yosys (FOSS Synthesis tool)"
		conda install -y $CONDA_FLAGS yosys
		check_exists yosys

		# nextpnr
		echo
		echo "Installing nextpnr (FOSS Place and Route tool)"
		conda install -y $CONDA_FLAGS nextpnr
		check_exists nextpnr-ice40
		;;
	*)
		;;
esac


# FPGA Programming tools
################################################
echo ""
echo "Installing programming tools in environment"
echo "-----------------------------------------"

# tinyfpga boards
if [ "$PLATFORM" = "tinyfpga_b2" ]; then
	echo
	echo "Installing tinyprog (tool for TinyFPGA B2 boards)"
	pip install tinyfpgab
	check_exists tinyfpgab
fi
if [ "$PLATFORM" = "tinyfpga_bx" ]; then
	echo
	echo "Installing tinyprog (tool for TinyFPGA BX boards)"
	pip install "git+https://github.com/tinyfpga/TinyFPGA-Bootloader#egg=tinyprog&subdirectory=programmer&subdirectory=programmer"
	check_exists tinyprog
fi
if [ "$PLATFORM" = "icebreaker" -o "$PLATFORM" = "ice40_hx8k_b_evn" -o "$PLATFORM" = "ice40_up5k_b_evn" ]; then
	echo
	echo "Installing iceprog (tool for FTDI)"
	conda install iceprog
	check_exists iceprog
fi

# fxload
if [ "$PLATFORM" = "opsis" -o "$PLATFORM" = "atlys" ]; then
	echo
	echo "Installing fxload (tool for Cypress FX2)"
	# conda install fxload
	check_exists fxload
fi

# FIXME: Remove this once @jimmo has finished his new firmware
# MimasV2Config.py
if [ "$PLATFORM" = "mimasv2" ]; then
	MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py
	echo
	echo "Installing MimasV2Config.py (mimasv2 flashing tool)"
	if [ ! -e $MIMASV2CONFIG ]; then
		wget https://raw.githubusercontent.com/numato/samplecode/master/FPGA/MimasV2/tools/configuration/python/MimasV2Config.py -O $MIMASV2CONFIG
		chmod a+x $MIMASV2CONFIG
	fi
	check_exists MimasV2Config.py
fi

# flterm
echo
echo "Installing flterm (serial terminal tool)"
conda install -y $CONDA_FLAGS flterm
check_exists flterm

# openocd for programming via Cypress FX2
echo
echo "Installing openocd (jtag tool for programming and debug)"
conda install -y $CONDA_FLAGS openocd=$OPENOCD_VERSION
check_version openocd $OPENOCD_VERSION


# C compiler toolchain
################################################
echo ""
echo "Installing C compiler toolchain"
echo "---------------------------------------"
if [ "$CPU" = "lm32" -o "$CPU" = "or1k" ]; then
	CPU_ARCH=$CPU
elif [ "$CPU" = "vexriscv" -o "$CPU" = "picorv32" -o "$CPU" = "minerva" ]; then
	CPU_ARCH=riscv32
fi

# binutils for the target
echo
echo "Installing binutils for ${CPU_ARCH} (assembler, linker, and other tools)"
conda install -y $CONDA_FLAGS binutils-${CPU_ARCH}-elf=$BINUTILS_VERSION
check_version ${CPU_ARCH}-elf-ld $BINUTILS_VERSION

# gcc for the target
echo
echo "Installing gcc for ${CPU_ARCH} ('bare metal' C cross compiler)"
conda install -y $CONDA_FLAGS gcc-${CPU_ARCH}-elf-nostdc=$GCC_VERSION
check_version ${CPU_ARCH}-elf-gcc $GCC_VERSION

# gdb for the target
#echo
#echo "Installing gdb for ${CPU_ARCH} (debugger)"
#conda install -y $CONDA_FLAGS gdb-${CPU_ARCH}-elf=$GDB_VERSION
#check_version ${CPU_ARCH}-elf-gdb $GDB_VERSION

# Zephyr SDK
################################################
if [ "$FIRMWARE" = "zephyr" ]; then
	SCRIPT_NAME="zephyr-sdk-$ZEPHYR_SDK_VERSION-setup.run"
	LOCAL_LOCATION="$BUILD_DIR/zephyr_sdk"

	DETECTED_SDK_LOCATION=""
	for DIR in "$LOCAL_LOCATION" "$ZEPHYR_SDK_INSTALL_DIR"; do
		if [ -d "$DIR" ]; then
			cat "$DIR/sdk_version" | grep -q $ZEPHYR_SDK_VERSION && DETECTED_SDK_LOCATION="$DIR"
		fi
	done

	echo
	if [ -d "$DETECTED_SDK_LOCATION" ]; then
		echo "Zephyr SDK $ZEPHYR_SDK_VERSION found in: $DETECTED_SDK_LOCATION"
		echo "---------------------------------------"
	else
		echo "Installing Zephyr SDK $ZEPHYR_SDK_VERSION"
		echo "---------------------------------------"
		(
			mkdir -p "$LOCAL_LOCATION"
			wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v$ZEPHYR_SDK_VERSION/$SCRIPT_NAME -O "$LOCAL_LOCATION/$SCRIPT_NAME"
			cd "$LOCAL_LOCATION"
			chmod u+x $SCRIPT_NAME
			./$SCRIPT_NAME -- -y -d "$PWD"
			rm $SCRIPT_NAME
		)
	fi
fi

# Python modules
################################################
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

if [ "$FIRMWARE" = "zephyr" ]; then
	# yaml for parsing configuration in Zephyr SDK
	echo
	echo "Installing yaml (python module)"
	conda install -y $CONDA_FLAGS pyyaml
	check_import yaml

	# elftools for Zephyr SDK
	echo
	echo "Installing elftools (python module)"
	pip install pyelftools
	check_import elftools

	# west tool for building Zephyr
	echo
	echo "Installing west (pyhton module)"
	pip install west
	check_import west

	# pykwalify for building Zephyr
	echo
	echo "Installing pykwalify (pyhton module)"
	pip install pykwalify
	check_import pykwalify.core
fi

# git commands
echo ""
echo "Updating git config"
echo "-----------------------"
(
	cd $TOP_DIR
	git config status.submodulesummary 1
	git config push.recurseSubmodules check
	git config diff.submodule log
	git config checkout.recurseSubmodules 1
	git config alias.sdiff '!'"git diff && git submodule foreach 'git diff'"
	git config alias.spush 'push --recurse-submodules=on-demand'
)
echo ""
echo "Updating git submodules"
echo "-----------------------"
(
	cd $TOP_DIR
	git submodule update --recursive --init
	git submodule foreach \
		git submodule update --recursive --init
	git submodule status --recursive
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
