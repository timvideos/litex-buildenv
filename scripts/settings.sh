#!/bin/bash

# Settings for the get-env.sh and setup-env.sh scripts

BOARD=${BOARD:-opsis}

BUILD_DIR=$TOP_DIR/build
THIRD_DIR=$TOP_DIR/third_party
CONDA_DIR=$BUILD_DIR/conda

BINUTILS_VERSION=2.26
GCC_VERSION=4.9.3
SDCC_VERSION=3.5.0
OPENOCD_VERSION=0.10.0-dev
