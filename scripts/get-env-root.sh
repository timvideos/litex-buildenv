#!/bin/bash

apt-get install -y realpath

if [ "`whoami`" != "root" ]
then
    echo "Please use sudo to run this script!"
    exit 1
fi

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)

set -x
set -e

apt-get install -y wget
apt-get install -y build-essential
# Need gpg to do the unencryption of Xilinx tools
apt-get install -y gnupg
# migen
# iverilog and gtkwave are needed for migen
apt-get install -y iverilog gtkwave
# FIXME: Also need to install the vpi module....
# cd vpi
# make all
# sudo make install

# misoc
# Nothing needed
# FIXME: Also need to install toools....
# cd tools
# make
# sudo make install

# liteeth
# Nothing needed

apt-get install -y libreadline-dev libusb-1.0-0-dev libftdi-dev python-yaml fxload

# Get the vizzini module needed for the Atlys board
apt-get install -y software-properties-common
add-apt-repository -y ppa:timvideos/fpga-support
apt-get update
apt-get install -y vizzini-dkms
