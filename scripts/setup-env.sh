#!/bin/bash

CALLED=$_
[[ $CALLED != $0 ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build


if [ $SOURCED = 0 ]; then
  echo "You must source this script, rather then try and run it."
  echo ". $SETUP_SRC"
  exit 1
fi

if [ ! -z $HDMI2USB_ENV ]; then
  echo "Already sourced this file."
  return
fi

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"

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
CONDA_DIR=$SETUP_DIR/build/conda
export PATH=$CONDA_DIR/bin:$PATH

# migen
MIGEN_DIR=$BUILD_DIR/migen
export PYTHONPATH=$MIGEN_DIR:$PYTHONPATH
python3 -c "import migen" || (echo "migen broken"; return)

# misoc
MISOC_DIR=$BUILD_DIR/misoc
export PYTHONPATH=$MISOC_DIR:$PYTHONPATH
python3 -c "import misoclib" || (echo "misoc broken"; return)

# liteeth
LITEETH_DIR=$BUILD_DIR/liteeth
export PYTHONPATH=$LITEETH_DIR:$PYTHONPATH
python3 -c "import liteeth" || (echo "liteeth broken"; return)

# libfpgalink
MAKESTUFF_DIR=$BUILD_DIR/makestuff
export LD_LIBRARY_PATH=$MAKESTUFF_DIR/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$MAKESTUFF_DIR/libs/libfpgalink/examples/python/:$PYTHONPATH
python3 -c "import fl" || (echo "libfpgalink broken"; return)

alias python=python3

HDMI2USB_ENV=1
