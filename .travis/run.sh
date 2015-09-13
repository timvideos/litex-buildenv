#!/bin/bash

. scripts/setup-env.sh

set +x
set -e

BOARDS="atlys opsis"

for BOARD in $BOARDS; do
	TARGETS="base hdmi2usb"
	# FIXME: Get hdmi2ethernet working on the Opsis
	if [ "$BOARD" = "atlys" ]; then
		TARGETS="$TARGETS hdmi2ethernet"
	fi

	for TARGET in $TARGETS; do
		echo ""
		echo ""
		echo ""
		echo "============================================="
		echo "- $BOARD $TARGET"
		echo "============================================="
		# Output the commands available to make it easier to debug.
		echo ""
		echo "- make help ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make help

		echo ""
		echo ""
		echo ""
		echo "- make gateware"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make gateware

		echo ""
		echo ""
		echo ""
		echo "- make firmware ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make firmware

		echo ""
		echo ""
		echo ""
		echo "- make clean ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
done
