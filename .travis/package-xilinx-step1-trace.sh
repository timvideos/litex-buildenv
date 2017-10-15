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
STRACE_LOG=$BASE/strace.log
if [ ! -z $PLATFORMS ]; then
	echo "\$PLATFORMS is set to '$PLATFORMS', please unset it."
	exit 1
fi
if [ ! -z $TARGETS ]; then
	echo "\$TARGETS is set to '$TARGETS', please unset it."
	exit 1
fi

(
	echo "Deleting previous builds..."
	cd build
	# Delete all the previous builds
	rm -rf *_*_*
)

exec strace -e trace=file,process -f -o ${STRACE_LOG} bash $SETUP_DIR/build.sh
