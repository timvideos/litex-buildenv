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
		echo "- make help ---------------------------------"
		BOARD=$BOARD TARGET=$TARGET make help

		# FIXME: Add ability to compile gateware.

		echo "- make firmware -----------------------------"
		BOARD=$BOARD TARGET=$TARGET make firmware

		echo "- make clean --------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
done
