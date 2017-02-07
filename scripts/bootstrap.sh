#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

if [ -z "$GITHUB_USER" ]; then
  GITHUB_USER=timvideos
fi
GIT_REPO=https://github.com/$GITHUB_USER/HDMI2USB-misoc-firmware.git
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
  sudo -E ./scripts/download-env-root.sh || exit 1
else
  echo "Aborting.."
  exit 1
fi
./scripts/download-env.sh || exit 1

# Check to see whether they've installed a Xilinx license file yet
if [ ! -e "$HOME/.Xilinx/Xilinx.lic" ]; then
  echo "Bootstrap: Set up complete."
  echo "Bootstrap: Failed to find a license file in ~/.Xilinx/Xilinx.lic"
  echo "Bootstrap: You can't build HDMI2USB-misoc-firmware without Xilinx ISE Design Suite"
  echo "Bootstrap: See scripts/README.md for instructions on how to obtain a license"
else
  echo "Bootstrap: Set up complete, you're good to go!";
fi
