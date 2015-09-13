#!/bin/bash


SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build


set -x
set -e

echo "             This script is: $SETUP_SRC"
echo "         Firmware directory: $TOP_DIR"
echo "         Build directory is: $BUILD_DIR"

if [ ! -d $BUILD_DIR ]; then
	mkdir -p $BUILD_DIR
fi

# gcc+binutils for the target
CONDA_DIR=$SETUP_DIR/build/conda
export PATH=$CONDA_DIR/bin:$PATH
(
	if [ ! -d $CONDA_DIR ]; then
		cd $BUILD_DIR
		wget -c https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
		chmod a+x Miniconda3-latest-Linux-x86_64.sh
	        ./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b
		conda config --set always_yes yes --set changeps1 no
		conda update -q conda
	fi
	conda config --add channels timvideos
	conda install binutils-lm32-elf
	conda install gcc-lm32-elf
)

# migen
MIGEN_DIR=$BUILD_DIR/migen
(
	# Get iverilog
	sudo apt-get install -y iverilog
	# Install gtkwave
	sudo apt-get install -y gtkwave

	if [ ! -d $MIGEN_DIR ]; then
		cd $BUILD_DIR
		git clone https://github.com/m-labs/migen.git
		cd migen
	else
		cd $MIGEN_DIR
		git pull
	fi
	cd vpi
	make all
	sudo make install
)
export PYTHONPATH=$MIGEN_DIR:$PYTHONPATH
python3 -c "import migen"

# misoc
MISOC_DIR=$BUILD_DIR/misoc
(
	if [ ! -d $MISOC_DIR ]; then
		cd $BUILD_DIR
		git clone https://github.com/m-labs/misoc.git
		cd misoc
	else
		cd $MISOC_DIR
		git pull
	fi
	git submodule init
	git submodule update
	cd tools
	make
	sudo make install
)
export PYTHONPATH=$MISOC_DIR:$PYTHONPATH
python3 -c "import misoclib"

# liteeth
LITEETH_DIR=$BUILD_DIR/liteeth
(
	if [ ! -d $LITEETH_DIR ]; then
		cd $BUILD_DIR
		git clone https://github.com/enjoy-digital/liteeth.git
		cd liteeth
	else
		cd $LITEETH_DIR
		git pull
	fi
)
export PYTHONPATH=$LITEETH_DIR:$PYTHONPATH
python3 -c "import liteeth"

# libfpgalink
MAKESTUFF_DIR=$BUILD_DIR/makestuff
(
	sudo apt-get install -y libreadline-dev libusb-1.0-0-dev python-yaml sdcc fxload

	if [ ! -d $MAKESTUFF_DIR ]; then
		cd $BUILD_DIR
		wget -qO- http://tiny.cc/msbil | tar zxf -
		cd makestuff/libs
		../scripts/msget.sh makestuff/libfpgalink
		cd libfpgalink
	else
		cd $MAKESTUFF_DIR
		cd libs/libfpgalink
	fi
	make deps
)
export LD_LIBRARY_PATH=$MAKESTUFF_DIR/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$MAKESTUFF_DIR/libs/libfpgalink/examples/python/:$PYTHONPATH
python3 -c "import fl"

USER=$(whoami)
# Load custom udev rules
(
	cd $SETUP_DIR
	sudo cp -uf 52-hdmi2usb.rules /etc/udev/rules.d/
	sudo adduser $USER dialout
)
# Get the vizzini module needed for the Atlys board
(
	sudo apt-get install -y software-properties-common
	sudo add-apt-repository -y ppa:timvideos/fpga-support
	sudo apt-get update
	sudo apt-get install -y vizzini-dkms
)

echo "Completed.  To load environment:"
echo "source HDMI2USB-misoc-firmware/scripts/setup-env.sh"
