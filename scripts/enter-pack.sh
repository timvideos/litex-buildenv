#!/bin/bash

### This script is supposed to be sourced rather than being run.
### It resembles the functionality of enter-env.sh, but is
### supposed to use a conda-pack package.
###
### The script looks for an lxbe-env environment. If it's not
### installed, it takes lxbe-env.tar.gz or a file provided as
### a parameter to this script as source for installation.

[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC="$(realpath ${BASH_SOURCE[0]})"
SETUP_DIR="$(dirname "${SETUP_SRC}")"
TOP_DIR="$(realpath "${SETUP_DIR}/..")"

if [ $SOURCED = 0 ]; then
	echo "You must source this script, rather than try and run it."
	echo ". $SETUP_SRC"
	exit 1
fi

source "$SETUP_DIR/setup-helpers.sh"
source "$SETUP_DIR/settings.sh"

verify_system || return 1

echo ""
echo "Preparing environment"
echo "---------------------"

# This is the name of the new environment from which the pack will be created.
# Note that this name appears in the template file as well. These values should
# match each other.
ENV_NAME=lxbe-env

# This is the conda-pack file - either the one provided as a parameter or a
# default one.
ENV_FILE=${1:-$ENV_NAME.tar.gz}
ENV_PATH=$BUILD_DIR/$ENV_NAME

if [ -d $ENV_PATH ]; then
	echo "Using existing env found in $ENV_PATH. " \
		 "To rebuild it, remove the directory"
	EXISTING_ENV=1
elif [ ! -f $ENV_FILE ]; then
	echo "Provide a correct path to tar.gz with your environment. " \
		 "File $ENV_FILE not found."
	return 1
fi

if [ ! $EXISTING_ENV ]; then
	echo ""
	echo "Unpacking $ENV_FILE..."
	mkdir -p $ENV_PATH
	tar xf $ENV_FILE -C $ENV_PATH
	echo "Done!"
fi

#required to not rely on user site-packages
export PYTHONNOUSERSITE=1

echo ""
echo "Activating environment"
echo "----------------------"

source $ENV_PATH/bin/activate
conda-unpack

# This is required as conda-pack does not contain editable modules.
# This operation is idempotent though, so we don't need additional checks.
echo ""
echo "Installing local python modules"
echo "-------------------------------"
git submodule status --recursive

# lite
for LITE in $LITE_REPOS; do
	LITE_DIR=$THIRD_DIR/$LITE
	(
		echo
		cd $LITE_DIR
		echo "Installing $LITE from $LITE_DIR (local python module)"
		python setup.py develop
	)
	check_import $LITE || return 1
done

# enter-env serves as a verifier of environmental variables, tool versions etc
. $SETUP_DIR/enter-env.sh
