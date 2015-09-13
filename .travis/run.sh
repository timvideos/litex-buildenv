#!/bin/bash

. scripts/setup-env.sh

set +x
set -e

BOARDS="atlys opsis"
TARGETS="base hdmi2usb"

for BOARD in $BOARDS; do
	for TARGET in $TARGETS; do
		echo "============================================="
		echo "- $BOARD $TARGET"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make help
		echo "---------------------------------------------"

		# FIXME: Add ability to compile gateware.

		BOARD=$BOARD TARGET=$TARGET make firmware
		echo "---------------------------------------------"

		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
done
