#!/bin/bash

. scripts/setup-env.sh

ls -l $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport
if [ -f $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport ]; then
	HAVE_XILINX_ISE=1
else
	HAVE_XILINX_ISE=0
fi

set +x
set -e

if [ -z "$BOARD" ]; then
	BOARDS="atlys opsis"
else
	BOARDS="$BOARD"
fi

for BOARD in $BOARDS; do
	if [ -z "$TARGET" ]; then
		TARGETS="base hdmi2usb"
		# FIXME: Get hdmi2ethernet working on the Opsis
		# https://github.com/timvideos/HDMI2USB-misoc-firmware/issues/51
		if [ "$BOARD" = "atlys" ]; then
			TARGETS="$TARGETS hdmi2ethernet"
		fi
	else
		TARGETS="$TARGET"
	fi
	(
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
		echo "- make gateware ($BOARD $TARGET)"
		echo "---------------------------------------------"
		if [ $HAVE_XILINX_ISE -eq 0 ]; then
			echo "Skipping gateware"
		else
			FILTER=$PWD/.travis/run-make-gateware-filter.py BOARD=$BOARD TARGET=$TARGET make gateware
		fi

		if [ ! -z "$PROGS" ]; then
			for PROG in $PROGS; do
				echo ""
				echo ""
				echo ""
				echo "- make load-gateware ($PROG $BOARD $TARGET)"
				echo "---------------------------------------------"
				# Allow the programming to fail.
				PROG=$PROG BOARD=$BOARD TARGET=$TARGET make load-gateware || true
			done
		fi

		echo ""
		echo ""
		echo ""
		echo "- make clean ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
	done
	)
done
