#!/bin/bash

source scripts/setup-env.sh

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

#create "clean" file list before build
find |grep -v .git | sort > /tmp/filelist.before

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

		# We build the firmware first as it is very quick to build and
		# will let us find a whole classes of errors quickly.

		echo ""
		echo ""
		echo ""
		echo "- make firmware ($BOARD $TARGET) (prerun)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make firmware
		# https://github.com/timvideos/HDMI2USB-misoc-firmware/issues/83
		# We have to clean after doing this otherwise if the gateware
		# has a dependency on the firmware that isn't correctly working
		# the travis build will still pass.
		echo "- make clean ($BOARD $TARGET) (prerun)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean

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
				echo "- make load ($PROG $BOARD $TARGET)"
				echo "---------------------------------------------"
				# Allow the programming to fail.
				PROG=$PROG BOARD=$BOARD TARGET=$TARGET make load || true
			done
		fi

		# FIXME(https://github.com/timvideos/HDMI2USB-misoc-firmware/issues/83):
		# Check after a "make clean" that only the initial files
		# remain.
		echo ""
		echo ""
		echo ""
		echo "- make clean ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="
		
		#create file list after make clean
		find | grep -v .git | sort > /tmp/filelist.after
		
                echo ""
		echo ""
		echo ""
		if ! diff -u /tmp/filelist.before /tmp/filelist.after|grep -v "@@"|grep "+" > /dev/null; then
			echo "- make clean did not leave any generated files behind"
		else
			echo "- make clean left these files behind"
			echo "============================================="
			diff -u /tmp/filelist.before /tmp/filelist.after|grep -v "@@"|grep "+"
			echo "============================================="
			exit 1
		fi

	done
	)
done
