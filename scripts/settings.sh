#!/bin/bash

# Settings for the download-env.sh and setup-env.sh scripts
BUILD_DIR=$TOP_DIR/build
THIRD_DIR=$TOP_DIR/third_party
CONDA_DIR=$BUILD_DIR/conda

CONDA_VERSION=4.7.10
PYTHON_VERSION=3.7

# Python module versions
HDMI2USB_MODESWITCH_VERSION=0.0.1
HEXFILE_VERSION=0.1
CMAKE_VERSION=3.14.4

# Conda package versions
BINUTILS_VERSION=2.32
GCC_VERSION=9.1.0
SDCC_VERSION=3.5.0
OPENOCD_VERSION=0.10.0
RENODE_VERSION=v1.10.1

# Other tools versions
ZEPHYR_SDK_VERSION=0.11.1

# lite modules
LITE_REPOS="
	migen
	nmigen
	litex
	litex-boards
	litedram
	liteeth
	litepcie
	litesata
	litescope
	litevideo
	liteiclink
	"
