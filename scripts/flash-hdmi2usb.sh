#!/bin/sh

set -x
set -e

if [ ! -e ~/HDMI2USB-misoc-firmware/build ]; then
 echo "You need to build the firmware first.  Please see README.md"
 exit 1
fi

cd ~/HDMI2USB-misoc-firmware

source ~/HDMI2USB-misoc-firmware/scripts/setup-env.sh

echo "Attempting to load gateware; will attempt 3 times, errors are normal"

for loop in 1 2 3
do 
 PROG=fpgalink make load-gateware; sleep 2
done

make load-fx2-firmware; sleep 1
make connect-lm32

