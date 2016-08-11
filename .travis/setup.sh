#!/bin/bash

set -x
set -e

echo ""
echo ""
echo ""
echo "- Fetching non shallow to get git version"
echo "---------------------------------------------"
git fetch --unshallow && git fetch --tags
if [ z"$TRAVIS_BRANCH" != z ]; then
	echo "Fixing detached head"
	git branch -v
	git branch -D $TRAVIS_BRANCH
	git checkout -b $TRAVIS_BRANCH
	git branch -v
fi
GIT_REVISION=`git describe`
echo "============================================="

export HDMI2USB_UDEV_IGNORE=1

# Run the script once to check it works
time scripts/download-env.sh
# Run the script again to check it doesn't break things
time scripts/download-env.sh

set +x
set +e
. scripts/enter-env.sh
