#!/bin/bash

set -x
set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)

BASE=$TOP_DIR/build/package-xilinx
echo $BASE
mkdir -p $BASE

export PREFIX="/opt/Xilinx/"

# This is based on https://github.com/m-labs/migen/blob/master/tools/strace_tailor.sh
if [ ! -z "$PLATFORMS" ]; then
	echo "\$PLATFORMS is set to '$PLATFORMS', please unset it."
	exit 1
fi
if [ ! -z "$TARGETS" ]; then
	echo "\$TARGETS is set to '$TARGETS', please unset it."
	exit 1
fi

(
	echo "Deleting previous builds..."
	cd build
	# Delete all the previous builds
	rm -rf *_*_*
)

STRACE_LOG=$BASE/strace.log
if [ -f $STRACE_LOG ]; then
	echo "Deleting old strace log."
	rm -v $STRACE_LOG
fi

# curl -L https://github.com/airnandez/cluefs/releases/download/v0.5/cluefs-v0.5-linux-x86_64.tar.gz | tar -xz
# https://github.com/airnandez/cluefs
# cluefs --mount=/opt/Xilinx --shadow=/opt/Xilinx.real --out=/tmp/Xilinx.log --ro --csv

#exec strace -e trace=file,process -E LD_LIBRARY_PATH=/opt/Xilinx/Vivado/2017.3/lib/lnx64.o -f -o ${STRACE_LOG} 
bash $SETUP_DIR/build.sh
