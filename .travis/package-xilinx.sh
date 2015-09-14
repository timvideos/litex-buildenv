#!/bin/bash

set -x
set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)

for ARG in XILINX_PASSPHRASE_IN RACKSPACE_USER RACKSPACE_API; do
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
	export PROGS=fpgalink
	strace -e trace=file,process -f -o ${STRACE_LOG} bash $SETUP_DIR/run.sh
fi

STRACE_FILES=$BASE/strace.files.log
cat $STRACE_LOG | python $SETUP_DIR/package-xilinx-filter-strace.py $PREFIX > $STRACE_FILES

XILINX_DIR=$BASE/xilinx-stripped
if [ -d $XILINX_DIR ]; then
  rm -rf $XILINX_DIR
fi

mkdir -p $XILINX_DIR
cat $STRACE_FILES | xargs -d '\n' \
	cp --parents --no-dereference --preserve=all -t $XILINX_DIR

FILENAME="$BASE/xilinx-ise-$(git describe).tar.bz2"
echo $FILENAME
(
	cd $XILINX_DIR
	tar --preserve-permissions -jcvf $FILENAME opt
)
echo $XILINX_PASSPHRASE_IN | gpg --passphrase-fd 0 --cipher-algo AES256 -c $FILENAME

(
	cd $BASE
	TB_COMMAND="turbolift -u $RACKSPACE_USER -a $RACKSPACE_API --os-rax-auth iad upload -c xilinx"

	# Upload the tar bz
	$TB_COMMAND -s . --sync --pattern-match ".*\.gpg"
	# Upload the index file
	md5sum *.gpg | sort -k2 > index.txt
	$TB_COMMAND -s index.txt
)
