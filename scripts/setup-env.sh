#!/bin/bash

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build
THIRD_DIR=$TOP_DIR/third_party


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

# gcc+binutils for the target
CONDA_DIR=$BUILD_DIR/conda
export PATH=$CONDA_DIR/bin:$PATH

# migen
MIGEN_DIR=$THIRD_DIR/migen
export PYTHONPATH=$MIGEN_DIR:$PYTHONPATH
python3 -c "import migen" || (echo "migen broken"; return)

# misoc
MISOC_DIR=$THIRD_DIR/misoc
export PYTHONPATH=$MISOC_DIR:$PYTHONPATH
$MISOC_DIR/tools/flterm --help || (echo "misoc flterm broken"; return)
python3 -c "import misoclib" || (echo "misoc broken"; return)

# liteeth
LITEETH_DIR=$THIRD_DIR/liteeth
export PYTHONPATH=$LITEETH_DIR:$PYTHONPATH
python3 -c "import liteeth" || (echo "liteeth broken"; return)

# libfpgalink
MAKESTUFF_DIR=$BUILD_DIR/makestuff
export LD_LIBRARY_PATH=$MAKESTUFF_DIR/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$MAKESTUFF_DIR/libs/libfpgalink/examples/python/:$PYTHONPATH
python3 -c "import fl" || (echo "libfpgalink broken"; return)

alias python=python3

export HDMI2USB_ENV=1
