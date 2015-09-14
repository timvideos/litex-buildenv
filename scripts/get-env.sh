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

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
	mkdir -p $BUILD_DIR
fi

sudo apt-get install -y build-essential

# Xilinx ISE

# --------
# Save the passphrase to a file so we don't echo it in the logs
XILINX_PASSPHRASE_FILE=$(tempfile)
trap "rm -f -- '$XILINX_PASSPHRASE_FILE'" EXIT
set +x
if [ ! -z "$XILINX_PASSPHRASE" ]; then
	echo $XILINX_PASSPHRASE >> $XILINX_PASSPHRASE_FILE
else
	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
fi
set -x
# --------

if [ -f $XILINX_PASSPHRASE_FILE ]; then
	# Need gpg to do the unencryption
	sudo apt-get install -y gnupg

	XILINX_DIR=$BUILD_DIR/Xilinx
	if [ ! -d "$XILINX_DIR" ]; then
		(
			cd $BUILD_DIR
			mkdir Xilinx
			cd Xilinx

			wget -q http://xilinx.timvideos.us/index.txt -O xilinx-details.txt
			XILINX_TAR_INFO=$(cat xilinx-details.txt | grep tar.bz2.gpg | tail -n 1)
			XILINX_TAR_FILE=$(echo $XILINX_TAR_INFO | sed -e's/[^ ]* //' -e's/.gpg$//')
			XILINX_TAR_MD5=$(echo $XILINX_TAR_INFO | sed -e's/ .*//')

			# This setup was taken from https://github.com/m-labs/artiq/blob/master/.travis/get-xilinx.sh
			wget -c http://xilinx.timvideos.us/${XILINX_TAR_FILE}.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 ${XILINX_TAR_FILE}.gpg
			tar -xjf $XILINX_TAR_FILE

			# Relocate ISE from /opt to $XILINX_DIR
			for i in $(grep -Rsn "/opt/Xilinx" $XILINX_DIR/opt | cut -d':' -f1)
			do
				sed -i -e "s!/opt/Xilinx!$XILINX_DIR/opt/Xilinx!g" $i
			done

			wget -c http://xilinx.timvideos.us/Xilinx.lic.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 Xilinx.lic.gpg

			git clone https://github.com/mithro/impersonate_macaddress
			cd impersonate_macaddress
			make
		)
	fi
	export MISOC_EXTRA_CMDLINE="-Ob ise_path $XILINX_DIR/opt/Xilinx/"
	# Reserved MAC address from documentation block, see
	# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
	export XILINXD_LICENSE_FILE=$XILINX_DIR
	export MACADDR=90:10:00:00:00:01
	#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
	#ls -l $LD_PRELOAD

	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
else
	XILINX_DIR=/
fi
echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"

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
	make deps 2>&1 | grep -E "^make"
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
