#!/bin/bash

set -x
set -e

#GIT_REPO=https://github.com/timvideos/HDMI2USB-misoc-firmware.git
GIT_REPO=https://github.com/xfxf/HDMI2USB-misoc-firmware
GIT_BRANCH=scripts

sudo apt-get install -y git realpath
cd ~

if [ -e HDMI2USB-misoc-firmware ]; then
 cd HDMI2USB-misoc-firmware
 #git pull
else
 git clone $GIT_REPO
 cd HDMI2USB-misoc-firmware
fi

git checkout $GIT_BRANCH
source ./scripts/get-env.sh 

