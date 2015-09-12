#!/bin/bash

. scripts/setup-env.sh

set -x

BOARDS="atlys opsis"
TARGETS="base hdmi2usb"

for BOARD in $BOARDS; do
	for TARGET in $TARGETS; do
		echo "---------------------------------------------"
		echo "- $BOARD $TARGET"
		echo "---------------------------------------------"

		BOARD=$BOARD TARGET=$TARGET make help

		# FIXME: Add ability to compile gateware.

		BOARD=$BOARD TARGET=$TARGET make lm32-firmware
		BOARD=$BOARD TARGET=$TARGET make fx2-firmware

		BOARD=$BOARD TARGET=$TARGET make clean
	done
done
