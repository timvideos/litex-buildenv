#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

if [ -z "$GITHUB_USER" ]; then
  GITHUB_USER=timvideos
fi
if [ -z "$GITHUB_REPO" ]; then
  GITHUB_REPO=litex-buildenv
fi

GIT_REPO=https://github.com/$GITHUB_USER/$GITHUB_REPO.git
if [ -z "$GIT_BRANCH" ]; then
  GIT_BRANCH=master
fi

TMOUT=5

if ! realpath --help > /dev/null 2>&1; then
 echo "realpath not found - aborting.."
 exit 1
fi

if ! git help > /dev/null 2>&1; then
 echo "git not found - aborting.."
 exit 1
fi

if [ -e $GITHUB_REPO ]; then
 cd $GITHUB_REPO || exit 1
else
 git clone --recurse-submodules $GIT_REPO || exit 1
 cd $GITHUB_REPO
 git checkout $GIT_BRANCH || exit 1
fi

# Setup things needed by download-env.sh script
if lsb_release -i | grep -q "Debian|Ubuntu"; then
 ./scripts/debian-setup.sh
else
 if ! wget --help > /dev/null 2>&1; then
  echo "wget not found - aborting.."
  exit 1
 fi

 if ! make --help > /dev/null 2>&1; then
  echo "make not found - aborting.."
  exit 1
 fi

 if ! grep --help > /dev/null 2>&1; then
  echo "grep not found - aborting.."
  exit 1
 fi

 if ! sed --help > /dev/null 2>&1; then
  echo "sed not found - aborting.."
  exit 1
 fi
fi

./scripts/download-env.sh || exit 1

echo "Bootstrap: Set up complete, you're good to go!";
