#! /bin/bash

SETUP_SRC=$(realpath ${BASH_SOURCE[@]})
SETUP_DIR=$(dirname $SETUP_SRC)
USER=$(whoami)

BINUTILS_URL=https://ftp.gnu.org/gnu/binutils/binutils-2.25.tar.gz
GCC_URL=https://ftp.gnu.org/gnu/gcc/gcc-4.9.3/gcc-4.9.3.tar.bz2
TARGET=lm32-elf

BUILD_DIR=$SETUP_DIR/../build
GNU_DIR=$BUILD_DIR/gnu
OUTPUT_DIR=$GNU_DIR/output
mkdir -p $OUTPUT_DIR

export PATH=$OUTPUT_DIR/bin:$PATH

set -x
set -e

sudo apt-get install -y build-essential wget
sudo adduser $USER dialout

# Get and build gcc+binutils for the target
(
	cd $GNU_DIR
	# Download binutils + gcc
	(
		mkdir -p download
		cd download
		wget -c $BINUTILS_URL
		wget -c $GCC_URL
	)

	# Build binutils for target
	sudo apt-get install -y texinfo
	(
		tar -zxvf ./download/binutils-*.tar.gz
		cd binutils-*
		mkdir -p build && cd build
		../configure --prefix=$OUTPUT_DIR --target=$TARGET
		make
		make install
	)

	# Build gcc for target
	sudo apt-get install -y libgmp-dev libmpfr-dev libmpc-dev
	(
		tar -jxvf ./download/gcc-*.tar.bz2
		cd gcc-*
		rm -rf libstdc++-v3
		mkdir -p build && cd build
		../configure --prefix=$OUTPUT_DIR --target=$TARGET --enable-languages="c,c++" --disable-libgcc --disable-libssp
		make
		make install
	)
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
)

# build exar-uart-driver
(
	cd $BUILD_DIR
	# Build the vizzini-source package
	rm -fr exar-uart-driver
	git clone https://github.com/mithro/exar-uart-driver
	cd exar-uart-driver
	sudo apt-get install linux-headers-generic debhelper module-assistant
	dpkg-buildpackage -rfakeroot
	# Install the vizzini-source package
	sudo dpkg --install ../vizzini-source_*_all.deb
	sudo apt-get -f install
	# Use module assistant to build and install a package containing modules for
	# your current kernel.
	sudo m-a b-i vizzini
)

sudo apt-get install -y gtkwave

echo "Completed.  To load environment:"
echo "source HDMI2USB-misoc-firmware/scripts/setup-env.sh"

