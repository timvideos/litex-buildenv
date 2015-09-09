#! /bin/bash

SETUP_SRC=$(realpath ${BASH_SOURCE[@]})
SETUP_DIR=$(dirname $SETUP_SRC)
USER=$(whoami)

BUILD_DIR=$SETUP_DIR/../build
CONDA_DIR=$SETUP_DIR/build/conda
OUTPUT_DIR=$GNU_DIR/output
mkdir -p $OUTPUT_DIR

export PATH=$OUTPUT_DIR/bin:$PATH

set -x
set -e

# Get and build gcc+binutils for the target
(
	if [ ! -d $CONDA_DIR ]; then
		cd $BUILD_DIR
		wget -c https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
		chmod a+x Miniconda3-latest-Linux-x86_64.sh
	        ./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b
	fi
	export PATH=$CONDA_DIR/bin:$PATH
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
	sudo python3 setup.py install
	cd migen/vpi
	make all
	sudo make install
)

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

# Get liteeth
(
	cd $BUILD_DIR
	rm -fr liteeth
	git clone https://github.com/enjoy-digital/liteeth.git
	cd liteeth
	sudo python3 setup.py install
)

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
# Load custom udev rules
(
	cd $SETUP_DIR
	sudo cp -uf 52-hdmi2usb.rules /etc/udev/rules.d/
	sudo adduser $USER dialout
)
# Get the vizzini module needed for the Atlys board
(
	sudo add-apt-repository ppa:timvideos/fpga-support
	sudo apt-get update
	sudo apt-get install vizzini-dkms
)

sudo apt-get install -y gtkwave

echo "Completed.  To load environment:"
echo "source HDMI2USB-misoc-firmware/scripts/setup-env.sh"
