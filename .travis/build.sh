#!/bin/bash

# How long to wait for "make gateware" to finish.
# Normal LiteX targets should take no longer than 20ish minutes on a modern
# machine. We round up to 40mins.
export GATEWARE_TIMEOUT=${GATEWARE_TIMEOUT:-2700}
export GATEWARE_KILLOUT=$((GATEWARE_TIMEOUT+60))
if [ -x /usr/bin/timeout ]; then
	export GATEWARE_TIMEOUT_CMD="/usr/bin/timeout --kill-after=${GATEWARE_KILLOUT}s ${GATEWARE_TIMEOUT}s"
elif [ -x /usr/bin/timelimit ]; then
	export GATEWARE_TIMEOUT_CMD="/usr/bin/timelimit -T $GATEWARE_KILLOUT -t $GATEWARE_TIMEOUT"
fi

# Check for the Xilinx toolchain being downloaded
export XILINX_LOCAL_USER_DATA=no

GIT_REVISION=$TRAVIS_BRANCH/$(git describe)
ORIG_COMMITTER_NAME=$(git log -1 --pretty=%an)
ORIG_COMMITTER_EMAIL=$(git log -1 --pretty=%ae)

set +x
set -e

function filelist() {
	find | sort | grep -v "__pycache__" | grep -v "conda" | grep -v third_party
}

function build() {
	SPLIT_REGEX="^\([^.]*\)\.\?\(.*\)\$"

	if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
		echo "usage: setup FULL_PLATFORM TARGET FULL_CPU FIRMWARE"
		echo "  got: setup '$1' '$2' '$3' '$4'"
		return 1
	fi

	#export FULL_PLATFORM=$1
	export PLATFORM="$(echo $1 | sed -e"s/$SPLIT_REGEX/\1/")"
	export PLATFORM_EXPANSION="$(echo $1 | sed -e"s/$SPLIT_REGEX/\2/")"

	export TARGET="$2"

	#export FULL_CPU=$3
	export CPU="$(echo $3 | sed -e"s/$SPLIT_REGEX/\1/")"
	export CPU_VARIANT="$(echo $3 | sed -e"s/$SPLIT_REGEX/\2/")"

	if [ x$4 != x ]; then
		FIRMWARE="$4"
	else
		unset FIRMWARE
	fi

	echo "--"
	echo "PLATFORM=$PLATFORM PLATFORM_EXPANSION=$PLATFORM_EXPANSION"
	echo "TARGET=$TARGET"
	echo "CPU=$CPU CPU_VARIANT=$CPU_VARIANT"
	echo "FIRMWARE=$FIRMWARE"
	echo "--"

	(
	# Imports TARGET, PLATFORM, CPU and TARGET_BUILD_DIR from Makefile
	echo "- Entering environment"
	echo "---------------------------------------------"
	source scripts/enter-env.sh || exit 1
	echo "============================================="
	echo ""
	echo ""
	echo ""
	echo "- make info"
	echo "---------------------------------------------"
	make info
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make clean"
	echo "---------------------------------------------"
	make clean
	echo "============================================="

	# Create "clean" file list before build
	filelist > /tmp/filelist.before

	TITLE="$FULL_PLATFORM $TARGET $FULL_CPU $FIRMWARE"

	export LOGFILE=$TARGET_BUILD_DIR/output.$(date +%Y%m%d-%H%M%S).log
	echo "Using logfile $LOGFILE"
	echo ""
	echo ""
	echo ""
	echo "- Disk space free (before build)"
	echo "---------------------------------------------"
	df -h
	DF_BEFORE_BUILD="$(($(stat -f --format="%a*%S" .)))"
	echo "============================================="
	echo ""
	echo ""
	echo ""
	echo "============================================="
	echo "- $TITLE"
	echo "============================================="
	# Output the commands available to make it easier to debug.
	echo ""
	echo "- make help ($TITLE)"
	echo "---------------------------------------------"
	make help
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make test ($TITLE)"
	echo "---------------------------------------------"
	make test || exit 1
	echo "============================================="

	# We build the firmware first as it is very quick to build and
	# will let us find a whole classes of errors quickly.

	echo ""
	echo ""
	echo ""
	echo "- make firmware check ($TITLE)"
	echo "---------------------------------------------"
	make FIRMWARE=firmware firmware || exit 1
	echo "- Firmware version data"
	echo "---------------------------------------------"
	VERSION_DATA="$(find $TARGET_BUILD_DIR -name version_data.c)"
	if [ -z "$VERSION_DATA" ]; then
		echo "No firmware version_data.c file found!"
	else
		cat $VERSION_DATA

		if grep -q -- "??" $VERSION_DATA; then
			echo "Repository had unknown files, failing to build!"
			git submodule foreach --recursive git ls-files --exclude-standard --others
			git submodule foreach --recursive git status
			git status
			git diff
			# exit 1
		fi

		if grep -q -- "-dirty" $VERSION_DATA; then
			echo "Repository was dirty, failing to build!"
			git submodule foreach --recursive git ls-files --exclude-standard --others
			git submodule foreach --recursive git status
			git status
			git diff
			# exit 1
		fi
	fi
	echo "============================================="

	# https://github.com/timvideos/HDMI2USB-misoc-firmware/issues/83
	# We have to clean after doing this otherwise if the gateware
	# has a dependency on the firmware that isn't correctly working
	# the travis build will still pass.
	echo ""
	echo ""
	echo ""
	echo "- make firmware-clean ($TITLE) (prerun)"
	echo "---------------------------------------------"
	make firmware-clean
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make gateware ($TITLE)"
	echo "---------------------------------------------"
	if [ $HAVE_FPGA_TOOLCHAIN -eq 0 ]; then
		echo "Skipping gateware"
		make gateware-fake
	else
		# Sometimes Xilinx ISE gets stuck and will never complete, we
		# use timeout to prevent waiting here forever.
		# FIXME: Should this be in the Makefile instead?
		echo "Using $GATEWARE_TIMEOUT timeout (with '$GATEWARE_TIMEOUT_CMD')."
		export FILTER=$PWD/.travis/run-make-gateware-filter.py
		$GATEWARE_TIMEOUT_CMD time --verbose make gateware || exit 1
	fi
	echo "============================================="

	case "$FIRMWARE" in
	linux)
		echo ""
		echo ""
		echo ""
		echo "- make firmware ($TITLE - $FIRMWARE)"
		echo "---------------------------------------------"
		./scripts/build-linux.sh || exit 1
		echo "============================================="
		;;
	micropython)
		echo ""
		echo ""
		echo ""
		echo "- make firmware ($TITLE - $FIRMWARE)"
		echo "---------------------------------------------"
		./scripts/build-micropython.sh || exit 1
		echo "============================================="
		;;
	zephyr)
		echo ""
		echo ""
		echo ""
		echo "- make firmware ($TITLE - $FIRMWARE)"
		echo "---------------------------------------------"
		./scripts/build-zephyr.sh || exit 1
		echo "============================================="
		;;
	*)
		echo ""
		echo ""
		echo ""
		echo "- make firmware ($TITLE - $FIRMWARE)"
		echo "---------------------------------------------"
		make firmware || exit 1
		echo "============================================="
		;;
	esac

	echo ""
	echo ""
	echo ""
	echo "- make image ($TITLE)"
	echo "---------------------------------------------"
	make image
	echo "============================================="

	if [ ! -z "$PROGS" ]; then
		for PROG in $PROGS; do
			echo ""
			echo ""
			echo ""
			echo "- make load ($PROG $TITLE)"
			echo "---------------------------------------------"
			# Allow the programming to fail.
			PROG=$PROG make load || true
		done
	fi


	echo ""
	echo ""
	echo ""
	echo "- test in Renode ($TITLE)"
	echo "---------------------------------------------"
	./scripts/test-renode.sh || exit 1
	echo "============================================="

	# Save the resulting binaries into the prebuilt repo. The gateware
	# should always exist, but others might not.
	if [ -d "$PREBUILT_DIR" ]; then
		echo ""
		echo ""
		echo ""
		echo "- Adding built files to $(cd $COPY_DEST; svn info | grep "Repository Root:")"
		echo "---------------------------------------------"

		COPY_DEST="$PREBUILT_DIR/archive/$GIT_REVISION/$FULL_PLATFORM/$TARGET/$FULL_CPU/"

		svn mkdir --parents $COPY_DEST

		declare -a SAVE
		SAVE+="image*.bin" 				# Combined binary include gateware+bios+firmware
		# Gateware output for using
		SAVE+=("gateware/")				# All gateware parts
		# Software support files
		SAVE+=("software/include/")			# Generated headers+config needed for QEmu, micropython, etc
		SAVE+=("software/bios/bios.*")			# BIOS for soft-cpu inside the gateware
		SAVE+=("software/firmware/firmware.*")		# HDMI2USB firmware for soft-cpu inside the gateware
		SAVE+=("support/fx2.hex")			# Firmware for Cypress FX2 on some boards
		# Extra firmware
		SAVE+=("software/micropython/firmware.*")	# MicroPython
		SAVE+=("software/linux/firmware.*")		# Linux
		SAVE+=("software/zephyr/firmware.*")		# Zephyr
		# CSV files with csr/litescope/etc descriptions
		SAVE+=("test/")

		for TO_SAVE in ${SAVE[@]}; do
			echo
			if ! ls $TARGET_BUILD_DIR/$TO_SAVE >/dev/null 2>&1; then
				echo "Nothing to save! ($TO_SAVE)"
				continue
			else
				echo "Saving $TO_SAVE"
			fi

			TO_SAVE_DIR="$(dirname $TO_SAVE)"
			mkdir -p $COPY_DEST/$TO_SAVE_DIR
			cp -v -r -a $TARGET_BUILD_DIR/$TO_SAVE $COPY_DEST/$TO_SAVE_DIR
		done

		# Logs, version information, etc
		mkdir -p $COPY_DEST/logs/
		cp $TARGET_BUILD_DIR/software/firmware/version_data.c $COPY_DEST/logs/version_data.c
		cp $TARGET_BUILD_DIR/output.*.log $COPY_DEST/logs/

		find $COPY_DEST -empty -delete

		(
		cd $COPY_DEST
		sha256sum $(find -type f) > sha256sum.txt
		cat sha256sum.txt
		)
		export GIT_AUTHOR_EMAIL="$ORIG_COMMITTER_EMAIL"
		export GIT_AUTHOR_NAME="$ORIG_COMMITTER_NAME"
		export GIT_COMMITTER_EMAIL="robot@timvideos.us"
		export GIT_COMMITTER_NAME="TimVideos Robot"
		echo ""
		(
		cd $COPY_DEST
		echo $PWD
		ls -l -a .
		svn add --parents *
		)
		(
		cd $PREBUILT_DIR
		echo $PWD
		COMMIT_MSG=$(tempfile -s .msg)
		cat > $COMMIT_MSG <<EOF
Travis build #$TRAVIS_BUILD_NUMBER of $GIT_REVISION for PLATFORM=$FULL_PLATFORM TARGET=$TARGET CPU=$FULL_CPU FIRMWARE=$FIRMWARE

From https://github.com/$TRAVIS_REPO_SLUG/tree/$TRAVIS_COMMIT
$TRAVIS_COMIT_MESSAGE
EOF
		svn commit \
			--file $COMMIT_MSG \
			--non-interactive \
			--username "$GH_USER" \
			--password "$GH_TOKEN" \
		)
		echo "============================================="
	fi

	echo ""
	echo ""
	echo ""
	echo "- Disk space free (after build)"
	echo "---------------------------------------------"
	df -h
	echo ""
	DF_AFTER_BUILD="$(($(stat -f --format="%a*%S" .)))"
	awk "BEGIN {printf \"Build is using %.2f megabytes\n\",($DF_BEFORE_BUILD-$DF_AFTER_BUILD)/1024/1024}"
	echo "============================================="

	if [ ! -z "$CLEAN_CHECK" ]; then
		echo ""
		echo ""
		echo ""
		echo "- make clean ($FULL_PLATFORM $TARGET)"
		echo "---------------------------------------------"
		make clean || exit 1
		echo "============================================="

		# Check that make clean didn't leave anything behind
		filelist > /tmp/filelist.after
		echo ""
		echo ""
		echo ""
		diff -u /tmp/filelist.before /tmp/filelist.after > /tmp/filelist.diff
		if [ $(wc -l < /tmp/filelist.diff) -eq 0 ] ; then
			echo "- make clean did not leave any generated files behind"
		else
			echo "- make clean left these files behind"
			echo "============================================="
			cat /tmp/filelist.diff
			echo "============================================="
			exit 1
		fi
	fi
	); return $?
}

export FUNC=build
. .travis/run.inc.sh

echo ""
echo ""
echo ""
echo "Errors from failures..."
echo "============================================="

for F in $(find . -name 'output.*.log'); do
	echo ""
	echo ""
	echo $F
	echo "---------------------------------------------"
	cat $F
	echo "---------------------------------------------"
done

echo ""
echo ""
echo ""
echo "The following builds succeeded"
echo "============================================="

for S in ${SUCCESSES[@]}; do
	echo $S | sed -e's/+/ /g'
done
echo ""
echo ""
echo ""
echo "The following builds failed!"
echo "============================================="

for F in ${FAILURES[@]}; do
	echo $F | sed -e's/+/ /g'
done

echo ""
echo ""
echo ""
echo "============================================="

if [ ${#FAILURES[@]} -ne 0 ]; then
	echo "One or more builds failed :("
	exit 1
else
	echo "All builds succeeded! \\o/"
fi

