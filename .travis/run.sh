#!/bin/bash

. scripts/setup-env.sh

if [ -f $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport ]; then
	HAVE_XILINX_ISE=1
else
	HAVE_XILINX_ISE=0
fi

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
		echo "- make firmware ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make firmware

		echo ""
		echo ""
		echo ""
		echo "- make gatewaree ($BOARD $TARGET)"
		echo "---------------------------------------------"
		if [ $HAVE_XILINX_ISE -eq 0 ]; then
			echo "Skipping gateware"
		else
			BOARD=$BOARD TARGET=$TARGET make gateware
		fi

		echo ""
		echo ""
		echo ""
		echo "- make clean ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
done
