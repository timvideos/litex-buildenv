#!/bin/bash

set -e

SETUP_SRC=$(realpath ${BASH_SOURCE[@]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR/..)
BUILD_DIR=$TOP_DIR/build
PREBUILT_DIR=$BUILD_DIR/prebuilt

if [ ! -e $BUILD_DIR ]; then
	echo "$BUILD_DIR does not exist so it looks like the prerequisite tools may not be available"
	echo "They can be installed by running scripts/get-env-root.sh and scripts/get-env.sh"
	exit 1
fi

if [ -z "$HDMI2USB_ENV" ]; then
	echo "You appear to have not sourced the HDMI2USB settings."
	echo "Please run '. $SETUP_DIR/enter-env.sh' before running this script."
	exit 1
fi

GITHUB_URL=https://github.com/timvideos/HDMI2USB-firmware-prebuilt/

UPSTREAM_BRANCH=master
UPSTREAM_REMOTE=$(git remote -v | grep fetch | grep 'github.com/timvideos' | sed -e's/\t.*$//')
#UPSTREAM_GITREV=$(git merge-base $UPSTREAM_REMOTE/$UPSTREAM_BRANCH HEAD)
UPSTREAM_GITREV=$(git show-branch --merge-base $UPSTREAM_REMOTE/$UPSTREAM_BRANCH HEAD)
UPSTREAM_GITDESC=$(git describe $UPSTREAM_GITREV)
eval $(make info)

: ${PREBUILT_REPO:="timvideos/HDMI2USB-firmware-prebuilt"}
echo "   Prebuilt Repository: $PREBUILT_REPO"
echo ""
echo "       Upstream remote: $UPSTREAM_REMOTE"
echo "       Upstream branch: $UPSTREAM_BRANCH"
echo "      Upstream git rev: $UPSTREAM_GITREV"
echo " Upstream git describe: $UPSTREAM_GITDESC"
echo ""
echo "              Platform: $PLATFORM"
echo "                Target: $TARGET"
echo "                   CPU: $CPU"
echo ""
echo
DOWNLOAD_URL="$GITHUB_URL/trunk/archive/$UPSTREAM_BRANCH/$UPSTREAM_GITDESC/$PLATFORM/$TARGET/$CPU/"
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

echo ""
echo "Done"
echo ""
