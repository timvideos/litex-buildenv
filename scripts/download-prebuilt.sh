#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SCRIPT_SRC=$(realpath ${BASH_SOURCE[0]})
SCRIPT_DIR=$(dirname $SCRIPT_SRC)
TOP_DIR=$(realpath $SCRIPT_DIR/..)

if [ $SOURCED = 1 ]; then
        echo "You must run this script, rather then try to source it."
        echo "$SCRIPT_SRC"
        return
fi

if [ -z "$HDMI2USB_ENV" ]; then
        echo "You appear to not be inside the HDMI2USB environment."
	echo "Please enter environment with:"
	echo "  source scripts/enter-env.sh"
        exit 1
fi

# Imports TARGET, PLATFORM, CPU and TARGET_BUILD_DIR from Makefile
eval $(make env)

if [ -d $TARGET_BUILD_DIR ]; then
	echo "Build directory '$TARGET_BUILD_DIR' already exists."
	echo "Remove this directory with 'make clean' before running this script."
	exit 1
fi

set -e


GITHUB_URL=https://github.com/timvideos/HDMI2USB-firmware-prebuilt/

UPSTREAM_BRANCH=master
UPSTREAM_REMOTE=$(git remote -v | grep '(fetch)' | grep -E 'timvideos/(litex-buildenv|HDMI2USB-litex-firmware)' | sed -e's/\t.*$//')
#UPSTREAM_GITREV=$(git merge-base $UPSTREAM_REMOTE/$UPSTREAM_BRANCH HEAD)
UPSTREAM_GITREV=$(git show-branch --merge-base $UPSTREAM_REMOTE/$UPSTREAM_BRANCH HEAD)
UPSTREAM_GITDESC=$(git describe $UPSTREAM_GITREV)

: ${PREBUILT_REPO:="timvideos/HDMI2USB-firmware-prebuilt"}
echo ""
echo "   Prebuilt Repository: $PREBUILT_REPO"
echo ""
echo "       Upstream remote: $UPSTREAM_REMOTE"
echo "       Upstream branch: $UPSTREAM_BRANCH"
echo "      Upstream git rev: $UPSTREAM_GITREV"
echo " Upstream git describe: $UPSTREAM_GITDESC"
echo ""
make info
echo ""
echo
DOWNLOAD_URL="$GITHUB_URL/trunk/archive/$UPSTREAM_BRANCH/$UPSTREAM_GITDESC/$FULL_PLATFORM/$TARGET/$CPU/"
echo "Downloading"
echo " from '$DOWNLOAD_URL'"
echo "   to '$TARGET_BUILD_DIR'"
echo "---------------------------------------"
# archive/master/v0.0.3-696-g2f815c1/minispartan6/base/lm32
svn export --force $DOWNLOAD_URL $TARGET_BUILD_DIR | grep -v "^Export"

SHA256SUM_FILE="sha256sum.txt"
(
	cd $TARGET_BUILD_DIR
	echo ""
	echo "Checking sha256sum of downloaded files in '$TARGET_BUILD_DIR'..."
	sha256sum -c $SHA256SUM_FILE
)

# Rewriting the paths in the files.
(
	cd $TARGET_BUILD_DIR
	echo ""
	echo "Rewriting paths in files..."
	for FILE in $(awk '{ print $2 }' $SHA256SUM_FILE); do
		echo "$FILE: Done"
		sed -i -e"s%/home/travis/build/timvideos/HDMI2USB-litex-firmware%$TOP_DIR%" $FILE
	done
)

echo ""
echo "Gateware downloaded!"
echo ""
