#!/bin/bash

CALLED=$_
[[ $CALLED != $0 ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build

GNU_DIR=$BUILD_DIR/gnu
MIGEN_DIR=$BUILD_DIR/migen
MISOC_DIR=$BUILD_DIR/misoc
MAKESTUFF_DIR=$BUILD_DIR/makestuff

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"
echo " gnu toolchain installed at: $GNU_DIR"
echo "             migen found at: $MIGEN_DIR"
echo "             misoc found at: $MISOC_DIR"
echo "          fpgalink found at: $MAKESTUFF_DIR"

if [ $SOURCED = 0 ]; then
  echo "You must source this script, rather then try and run it."
  echo ". $SETUP_SRC"
  exit 1
fi

if [ ! -z $MISOC_ENV ]; then
  echo "Already have misoc environment."
  exit 1
fi

export LD_LIBRARY_PATH=$MAKESTUFF_DIR/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$MIGEN_DIR:$MISOC_DIR:$MAKESTUFF_DIR/libs/libfpgalink/examples/python/:$PYTHONPATH
export PATH=$GNU_DIR/output/bin:/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/:$PATH

alias python=python3
