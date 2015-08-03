#!/bin/bash

CALLED=$_
[[ $CALLED != $0 ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[@]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/../build)

echo $TOP_DIR

if [ $SOURCED = 0 ]; then
  echo "You must source this script, rather then try and run it."
  echo ". $SETUP_SRC"
  exit 1
fi

if [ ! -z $MISOC_ENV ]; then
  echo "Already have misoc environment."
  exit 1
fi

export LD_LIBRARY_PATH=$TOP_DIR/../makestuff/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$TOP_DIR/migen:$TOP_DIR/misoc:$TOP_DIR/../makestuff/libs/libfpgalink/examples/python/:$PYTHONPATH
export PATH=$TOP_DIR/gnu/output/bin:$PATH

alias python=python3
