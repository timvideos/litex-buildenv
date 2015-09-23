#!/bin/bash
apt-get install -y realpath
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

# libfpgalink
sudo apt-get install -y libreadline-dev libusb-1.0-0-dev python-yaml sdcc fxload

# Load custom udev rules
(
	cp -uf  ${BASH_SOURCE%/*}/52-hdmi2usb.rules /etc/udev/rules.d/
	sudo adduser $USER dialout
)

# Get the vizzini module needed for the Atlys board
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:timvideos/fpga-support
sudo apt-get update
sudo apt-get install -y vizzini-dkms
