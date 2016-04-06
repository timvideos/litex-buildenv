#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root. Not permitted"
    exit 1
fi

GIT_REPO=https://github.com/timvideos/HDMI2USB-misoc-firmware.git
if [ -z "$GIT_BRANCH" ]; then
  GIT_BRANCH=master
fi

TMOUT=5

if ! git help > /dev/null 2>&1; then
 yn=y
 #read -p "Install git to checkout the repository? (y/n) " yn
 if [ "$yn" = "y" -o "$yn" = "Y" ]; then
   sudo apt-get install -y git || exit 1
 else
   echo "Aborting.."
   exit 1
 fi
fi

if [ -e HDMI2USB-misoc-firmware ]; then
 echo "Existing checkout found (see HDMI2USB-misoc-firmware directory), please remove before running."
 exit 1
else
 git clone --recurse-submodules $GIT_REPO || exit 1
 cd HDMI2USB-misoc-firmware
 git checkout $GIT_BRANCH || exit 1
fi

yn=y
#read -p "Need to install packages as root. Continue? (y/n) " yn
if [ "$yn" = "y" -o "$yn" = "Y" -o -z "$yn" ]; then
  sudo -E ./scripts/get-env-root.sh || exit 1
else
  echo "Aborting.."
  exit 1
fi
./scripts/get-env.sh || exit 1
