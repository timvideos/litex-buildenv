#!/bin/bash

. scripts/setup-env.sh

set +x
set -e

BOARDS="atlys opsis"
TARGETS="base hdmi2usb"

for BOARD in $BOARDS; do
	for TARGET in $TARGETS; do
		echo ""
		echo ""
		echo ""
		echo "============================================="
		echo "- $BOARD $TARGET"
		echo "============================================="
		echo ""
		echo "- make help"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make help

		# FIXME: Add ability to compile gateware.

		echo ""
		echo ""
		echo ""
		echo "- make firmware"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make firmware

		echo ""
		echo ""
		echo ""
		echo "- make clean"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
done
