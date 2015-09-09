#!/bin/bash

CALLED=$_
[[ $CALLED != $0 ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build
CONDA_DIR=$SETUP_DIR/build/conda

MIGEN_DIR=$BUILD_DIR/migen
MISOC_DIR=$BUILD_DIR/misoc
LITEETH_DIR=$BUILD_DIR/liteeth
MAKESTUFF_DIR=$BUILD_DIR/makestuff

if [ $SOURCED = 0 ]; then
  echo "You must source this script, rather then try and run it."
  echo ". $SETUP_SRC"
  exit 1
fi

if [ ! -z $HDMI2USB_ENV ]; then
  echo "Already sourced this file."
  return
fi
HDMI2USB_ENV=1

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"

export LD_LIBRARY_PATH=$MAKESTUFF_DIR/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$MIGEN_DIR:$MISOC_DIR:$LITEETH_DIR:$MAKESTUFF_DIR/libs/libfpgalink/examples/python/:$PYTHONPATH
export PATH=$CONDA_DIR/bin:/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/:$PATH

alias python=python3
