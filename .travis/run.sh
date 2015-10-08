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

# Create "clean" file list before build
find | sort > /tmp/filelist.before

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
		
		# Copy built files
		if [ -z $GH_TOKEN  ]; then
			# Only if run by travis display error
			if [ ! -z $TRAVIS_BUILD_NUMBER  ]; then
				echo ""
				echo ""
				echo ""
				echo "- No Github token so unable to copy built files"
			fi
		else
			echo ""
			echo ""
			echo ""
			echo "- Fetching non shallow to get git version"
			echo "---------------------------------------------"
			git fetch --unshallow && git fetch --tags
			GIT_REVISION=`git describe`
			echo "============================================="
			COPY_REPO_OWNER="timvideos"
			COPY_REPO="HDMI2USB-firmware-prebuilt"
			COPY_DEST="archive/$GIT_REVISION/$BOARD/$TARGET"
			ORIG_COMMITTER_NAME=`git log -1 --pretty=%an`
			ORIG_COMMITTER_EMAIL=`git log -1 --pretty=%ae`
			echo ""
			echo ""
			echo ""
			echo "- Uploading built files to github.com/$COPY_REPO_OWNER/$COPY_REPO$COPY_DEST"
			echo "---------------------------------------------"
			rm -rf $COPY_REPO
			git clone https://$GH_TOKEN@github.com/$COPY_REPO_OWNER/$COPY_REPO.git			
			cd $COPY_REPO
			mkdir -p $COPY_DEST
			# Not currently built so use .bit instead
			#cp ../third_party/misoc/build/*.xsvf $COPY_DEST
			cp ../third_party/misoc/build/*.bit $COPY_DEST
			cp ../build/output.*.log $COPY_DEST
			echo ""
			echo "- Uploading .bit and logfile"
			# Only hdmi2usb is considered usable just now
			UNSTABLE_LINK="$BOARD/firmware/unstable"
			if [ "$TARGET" = "hdmi2usb" ]; then
				# Copy FX2 firmware
				cp ../firmware/fx2/hdmi2usb.hex $COPY_DEST
				# Create link to latest unstable build
				echo ""
				echo "- Uploading FX2 firmware"
				rm $UNSTABLE_LINK
				ln -s ../../$COPY_DEST $UNSTABLE_LINK
				echo ""
				echo "- Added symlink of $UNSTABLE_LINK -> $COPY_DEST"
			fi
			git config user.email "$ORIG_COMMITTER_EMAIL"
			git config user.name "$ORIG_COMMITTER_NAME"
			git add -A .
			git commit -a -m "Travis build #$TRAVIS_BUILD_NUMBER of $GIT_REVISION"
			git push --quiet origin master > /dev/null 2>&1
			cd ..
			rm -rf $COPY_REPO
			echo "============================================="
		fi

		echo ""
		echo ""
		echo ""
		echo "- make clean ($BOARD $TARGET)"
		echo "---------------------------------------------"
		BOARD=$BOARD TARGET=$TARGET make clean
		echo "============================================="

		# Check that make clean didn't leave anything behind
		find | sort > /tmp/filelist.after
                echo ""
		echo ""
		echo ""
		if ! diff -u /tmp/filelist.before /tmp/filelist.after > /tmp/filelist.diff; then
			echo "- make clean did not leave any generated files behind"
		else
			echo "- make clean left these files behind"
			echo "============================================="
			cat /tmp/filelist.diff | grep "^+"
			echo "============================================="
			exit 1
		fi

	done
	)
done
