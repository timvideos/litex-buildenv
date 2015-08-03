#!/bin/bash

set -x
set -e

sudo apt-get install git
git clone https://github.com/timvideos/HDMI2USB-misoc-firmware.git
cd HDMI2USB-misoc-firmware
git checkout scripts
source ./get-env.sh 

