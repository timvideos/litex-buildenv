#!/bin/bash

### This script is, in principle, similar to download-env.sh
### Notable differences:
### - download-env does not download everything, but depends on system variables
### - download-env installs LiteX submodules. This is not allowed here as
###   conda-pack fails when it finds editable pip modules
### - download-env downloads Zephyr SDK if needed. This script does not do it,
###   but will when the SDK conda package is created

SETUP_SRC="$(realpath ${BASH_SOURCE[0]})"
SETUP_DIR="$(dirname "${SETUP_SRC}")"
TOP_DIR="$(realpath "${SETUP_DIR}/..")"

source "$SETUP_DIR/setup-helpers.sh"
source "$SETUP_DIR/settings.sh"

verify_system || exit 1

set -e
set -u

# Ensure the build dir
mkdir -p $BUILD_DIR

echo ""
echo "Initializing environment"
echo "------------------------"
# Install and setup conda for downloading packages
export PATH=$CONDA_DIR/bin:$PATH:/sbin
(
	install_conda
)

echo ""
echo "Preparing packages"
echo "------------------"

# this file will contain final env description
ENV_FILE=$BUILD_DIR/environment.yml

# this file contains packages which versions are not specified in settings.sh
ENV_TEMPLATE=$SETUP_DIR/template-environment.yml

# This is the name of the new environment from which the pack will be created.
# Note that this name appears in the template file as well. These values should
# match each other
ENV_NAME=lxbe-env

# As conda environment yml format does not seem to allow variables and we want
# to rely on settings.sh to specify package versions, we programatically fill up
# the env file with proper versions.
cat $ENV_TEMPLATE > $ENV_FILE
echo "  - conda=$CONDA_VERSION" >> $ENV_FILE
echo "  - python=$PYTHON_VERSION" >> $ENV_FILE
echo "  - openocd=$OPENOCD_VERSION" >> $ENV_FILE

# This code is supposed to add entries for all architectures and toolchain
# flavors.
# Some conda packages are not there yet (namely x86_64 and lm32 with musl),
# so we comment these out.
for ARCH in or1k riscv32 lm32 x86_64; do
	if [[ "$ARCH" == "x86_64" ]]; then
		echo -n "#" >> $ENV_FILE
	fi
	echo "  - binutils-$ARCH-elf=$BINUTILS_VERSION" >> $ENV_FILE
	for FLAVOR in elf-nostdc elf-newlib linux-musl; do
		if [[ "$ARCH" == "x86_64" || ( "$ARCH" == "lm32"
									&& "$FLAVOR" == "linux-musl" ) ]]; then
			echo -n "#" >> $ENV_FILE
	fi
	echo "  - gcc-$ARCH-$FLAVOR=$GCC_VERSION" >> $ENV_FILE
	done
done

echo ""
echo "Preparing dependencies"
echo "----------------------"
cat $ENV_FILE

# This creates an lxbe-env environment.
conda env create -f $ENV_FILE

#required to not rely on user site-packages
export PYTHONNOUSERSITE=1

# We enter the conda env to install things via pip manually.
# This can't be done via the yml file because we invariably use the user's
# site-packages.
# Unfortunately, the activate/deactivate scripts have to have -e/-u disabled.
# This also applies to Renode package installation.
set +u
set +e
source activate $ENV_NAME

# We install Renode separately, no to polute the ENV_FILE with conda-forge repo.
# It is needed for mono.
conda install -y $CONDA_FLAGS -c antmicro -c conda-forge renode

set -u
set -e

# We're using pip install instead of putting it in the yml, because we want to
# ensure isolation.
# conda env create does not seem to take PYTHONNOUSERSITE=1 very seriously.
# We're not installing conda-pack from conda because it requires conda-forge
# source.
pip install conda-pack \
			tinyfpgab \
			progressbar2 \
			colorama \
			sphinx_rtd_theme \
			sphinx \
			pyelftools \
			west \
			pykwalify \
			"git+https://github.com/tinyfpga/TinyFPGA-Bootloader#egg=tinyprog&subdirectory=programmer&subdirectory=programmer" \
			git+https://github.com/mithro/hexfile.git \
			git+https://github.com/timvideos/HDMI2USB-mode-switch.git \
			"cmake==$CMAKE_VERSION"


# This has to be installed manually in the environment
MIMASV2CONFIG=$BUILD_DIR/conda/bin/MimasV2Config.py
echo
echo "Installing MimasV2Config.py (mimasv2 flashing tool)"
if [ ! -e $MIMASV2CONFIG ]; then
	wget https://raw.githubusercontent.com/numato/samplecode/master/FPGA/MimasV2/tools/configuration/python/MimasV2Config.py -O $MIMASV2CONFIG
	chmod a+x $MIMASV2CONFIG
fi
check_exists MimasV2Config.py

echo ""
echo "Working environment"
echo "-------------------"

conda env export

echo ""
echo "Creating a pack"
echo "---------------"

rm -f $BUILD_DIR/$ENV_NAME.tar.gz
conda pack -p $CONDA_DIR/envs/$ENV_NAME -o $BUILD_DIR/$ENV_NAME.tar.gz

# The activate/deactivate conda scripts have to have -e/-u disabled.
set +u
set +e
conda deactivate
set -e
set -u

echo ""
echo "Package created in $BUILD_DIR/$ENV_NAME.tar.gz!"
echo ""
