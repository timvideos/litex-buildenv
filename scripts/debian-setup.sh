#!/bin/bash

# Need realpath for finding where we are running from.
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

# Need wget to download conda in download-env.sh
apt-get install -y wget
# We are building C code, so need build-essential
apt-get install -y build-essential

# Need gpg to create the encrypted package of Xilinx tools for CI, not needed
# by normal developers.
#apt-get install -y gnupg

# gtkwave is needed for viewing the output of traces
apt-get install -y gtkwave

# FIXME: What needs python-yaml!?
apt-get install -y python-yaml

# aftpd is needed for tftp booting firmware
apt-get install -y atftpd

# These libraries are needed for working with the sim target
apt-get install -y openvpn libsdl1.2-dev

# FIXME: Work out if this stuff below is needed.
apt-get install -y software-properties-common
add-apt-repository -y ppa:timvideos/fpga-support
apt-get update
# Only need the udev rules (the full mode-switch tool is installed locally as
# part of the download-env.sh).
apt-get install -y hdmi2usb-udev || apt-get install -y hdmi2usb-mode-switch-udev

# Get the vizzini module, only needed for the Atlys board
#apt-get install -y vizzini-dkms
