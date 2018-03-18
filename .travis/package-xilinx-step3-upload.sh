#!/bin/bash

set -x
set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)

for ARG in RACKSPACE_USER RACKSPACE_API; do
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

(
	cd $BASE
	TB_COMMAND="turbolift --verbose --colorized -u $RACKSPACE_USER -a $RACKSPACE_API --os-rax-auth iad upload -c xilinx"

	# Upload the tar bz
	$TB_COMMAND -s . --sync --pattern-match ".*\.gpg"
	# Upload the index file
	md5sum *.gpg | sort -t- -k3,3V -k4,4n > index.txt
	cat index.txt
	$TB_COMMAND -s . --sync --pattern-match "index.txt"
)
