#!/bin/bash

set -x
set -e

#XILINX_PASSPHRASE
#RACKSPACE_USER
#RACKSPACE_API

export PREFIX="/opt/Xilinx/"

TB_COMMAND="turbolift -u $RACKSPACE_USER -a $RACKSPACE_API --os-rax-auth iad upload -c xilinx"

./build/migen/tools/strace_tailor.sh $PREFIX bash .travis/run.sh
cp $PREFIX/14.7/ISE_DS/ISE/bin/lin64/xreport opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/

FILENAME="xilinx-ise-$(git describe).tar.bz2"
echo $FILENAME

tar --preserve-permissions -jcvf $FILENAME opt
echo $XILINX_PASSPHRASE_IN | gpg --passphrase-fd 0 --cipher-algo AES256 -c $FILENAME

# Upload the tar bz
$TB_COMMAND -s . --sync --pattern-match ".*\.gpg"

# Generate an index file
md5sum *.gpg | sort -k2 > index.txt
$TB_COMMAND -s index.txt
