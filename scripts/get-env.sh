#!/bin/bash


SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build
CONDA_DIR=$SETUP_DIR/build/conda


set -x
set -e

mkdir -p $BUILD_DIR

# Get and build gcc+binutils for the target
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

# Get iverilog
(
	sudo apt-get install -y iverilog
)

# Get migen
(
	cd $BUILD_DIR
	rm -fr migen
	git clone https://github.com/m-labs/migen.git
	cd migen
	cd vpi
	make all
	sudo make install
)
export PYTHONPATH=$BUILD_DIR/migen:$PYTHONPATH
python3 -c "import migen"

# Get misoc
(
	cd $BUILD_DIR
	rm -fr misoc
	git clone https://github.com/m-labs/misoc.git
	cd misoc
	git submodule init
	git submodule update
	cd tools
	make
	sudo make install
)
export PYTHONPATH=$BUILD_DIR/misoc:$PYTHONPATH
python3 -c "import misoclib"

# Get liteeth
(
	cd $BUILD_DIR
	rm -fr liteeth
	git clone https://github.com/enjoy-digital/liteeth.git
)
export PYTHONPATH=$BUILD_DIR/liteeth:$PYTHONPATH
python3 -c "import liteeth"

# Get libfpgalink
(
	cd $BUILD_DIR
	sudo apt-get install -y libreadline-dev libusb-1.0-0-dev python-yaml sdcc fxload
	rm -fr makestuff
	wget -qO- http://tiny.cc/msbil | tar zxf -
	cd makestuff/libs
	../scripts/msget.sh makestuff/libfpgalink
	cd libfpgalink
	make deps
)
export LD_LIBRARY_PATH=$BUILD_DIR/makestuff/libs/libfpgalink/lin.x64/rel:$LD_LIBRARY_PATH
export PYTHONPATH=$BUILD_DIR/makestuff/libs/libfpgalink/examples/python/
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

sudo apt-get install -y gtkwave

echo "Completed.  To load environment:"
echo "source HDMI2USB-misoc-firmware/scripts/setup-env.sh"
