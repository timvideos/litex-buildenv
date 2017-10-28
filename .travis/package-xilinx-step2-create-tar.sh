#!/bin/bash

set -x
set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)

for ARG in XILINX_PASSPHRASE_IN; do
	if [ -z "${!ARG}" ]; then
		echo "$ARG not set"
		exit 1
	else
		echo "$ARG='${!ARG}'"
	fi
done

BASE=$TOP_DIR/build/package-xilinx
echo $BASE
mkdir -p $BASE

export PREFIX="/opt/Xilinx/"

# This is based on https://github.com/m-labs/migen/blob/master/tools/strace_tailor.sh
STRACE_LOG=$BASE/strace.log
if [ ! -f $STRACE_LOG ]; then
	echo "No strace log found at $STRACE_LOG"
	echo "Please run ./.travis/package-xilinx-step1-trace.sh"
	exit 1
fi

STRACE_FILES=$BASE/strace.files.log
#cat $STRACE_LOG | python $SETUP_DIR/package-xilinx-filter-strace.py $PREFIX > $STRACE_FILES
$SETUP_DIR/package-xilinx-cluefs-filter.py $STRACE_LOG > $STRACE_FILES

XILINX_DIR=$BASE/xilinx-stripped
if [ -d $XILINX_DIR ]; then
  rm -rf $XILINX_DIR
fi

echo ""
echo "Creating directories"
echo "--------------------------------------"
mkdir -p $XILINX_DIR
cat $STRACE_FILES | xargs -d '\n' \
	cp -v --parents --no-dereference --preserve=all -t $XILINX_DIR || true
echo "--------------------------------------"

FILENAME="$BASE/xilinx-tools-$(git describe).tar.bz2"
echo $FILENAME
(
	cd $XILINX_DIR
	echo ""
	echo "Creating tar file"
	echo "--------------------------------------"
	tar --preserve-permissions -jcvlf $FILENAME opt
	echo "--------------------------------------"
)
echo $XILINX_PASSPHRASE_IN | gpg --passphrase-fd 0 --cipher-algo AES256 -c $FILENAME
