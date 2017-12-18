#!/bin/bash

if [ -z "$PLATFORMS" ]; then
	if [ -z "$SKIP_PLATFORMS" ]; then
		SKIP_PLATFORMS="sim"
	fi
	if [ -z "$PLATFORM" ]; then
		PLATFORMS=$(ls targets/ | grep -v ".py" | grep -v "common" | grep -v "$SKIP_PLATFORMS" | sed -e"s+targets/++")
	else
		PLATFORMS="$PLATFORM"
	fi
fi
echo "Running with PLATFORMS='$PLATFORMS'"

source scripts/enter-env.sh || exit 1

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

ls -l $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport
if [ -f $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xreport ]; then
	HAVE_XILINX_ISE=1
else
	HAVE_XILINX_ISE=0
fi

set +x
set -e

function build() {
	export PLATFORM=$1
	export TARGET=$2
	export CPU=$3

	if [ -z "$PLATFORM" -o -z "$TARGET" -o -z "$CPU" ]; then
		echo "usage: build PLATFORM TARGET CPU"
		echo "  got: build '$PLATFORM' '$TARGET' '$CPU'"
		return 1
	fi

	# Create "clean" file list before build
	find | sort | grep -v "__pycache__" > /tmp/filelist.before

	export TARGET_BUILD_DIR=$PWD/build/${PLATFORM}_${TARGET}_${CPU}
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
	echo "- $PLATFORM $TARGET $CPU"
	echo "============================================="
	# Output the commands available to make it easier to debug.
	echo ""
	echo "- make help ($PLATFORM $TARGET $CPU)"
	echo "---------------------------------------------"
	make help
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make test ($PLATFORM $TARGET $CPU)"
	echo "---------------------------------------------"
	make test || return 1
	echo "============================================="

	# We build the firmware first as it is very quick to build and
	# will let us find a whole classes of errors quickly.

	echo ""
	echo ""
	echo ""
	echo "- make firmware ($PLATFORM $TARGET $CPU) (prerun)"
	echo "---------------------------------------------"
	make -j4 firmware || return 1
	echo "- Firmware version data"
	echo "---------------------------------------------"
	VERSION_DATA="$(find $TARGET_BUILD_DIR -name version_data.c)"
	if [ -z "$VERSION_DATA" ]; then
		echo "No firmware version_data.c file found!"
	else
		cat $VERSION_DATA

		if grep -q -- "??" $VERSION_DATA; then
			echo "Repository had unknown files, failing to build!"
#			return 1
		fi

		if grep -q -- "-dirty" $VERSION_DATA; then
			echo "Repository was dirty, failing to build!"
#			return 1
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
	echo "- make firmware-clean ($PLATFORM $TARGET $CPU) (prerun)"
	echo "---------------------------------------------"
	make firmware-clean
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make gateware ($PLATFORM $TARGET $CPU)"
	echo "---------------------------------------------"
	if [ $HAVE_XILINX_ISE -eq 0 ]; then
		echo "Skipping gateware"
		make gateware-fake
	else
		# Sometimes Xilinx ISE gets stuck and will never complete, we
		# use timeout to prevent waiting here forever.
		# FIXME: Should this be in the Makefile instead?
		echo "Using $GATEWARE_TIMEOUT timeout (with '$GATEWARE_TIMEOUT_CMD')."
		export FILTER=$PWD/.travis/run-make-gateware-filter.py
		$GATEWARE_TIMEOUT_CMD time --verbose make gateware || return 1
	fi
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make firmware ($PLATFORM $TARGET $CPU)"
	echo "---------------------------------------------"
	make -j4 firmware || return 1
	echo "============================================="

	echo ""
	echo ""
	echo ""
	echo "- make image ($PLATFORM $TARGET $CPU)"
	echo "---------------------------------------------"
	make image || true
	echo "============================================="

	if [ ! -z "$PROGS" ]; then
		for PROG in $PROGS; do
			echo ""
			echo ""
			echo ""
			echo "- make load ($PROG $PLATFORM $TARGET $CPU)"
			echo "---------------------------------------------"
			# Allow the programming to fail.
			PROG=$PROG make load || true
		done
	fi

	# Save the resulting binaries into the prebuilt repo. The gateware
	# should always exist, but others might not.
	if [ ! -z "$PREBUILT_DIR" ]; then
		COPY_DEST="$PREBUILT_DIR/archive/$GIT_REVISION/$PLATFORM/$TARGET/$CPU/"
		echo ""
		echo ""
		echo ""
		echo "- Adding built files to github.com/$PREBUILT_REPO_OWNER/$PREBUILT_REPO"
		echo "---------------------------------------------"

		mkdir -p $COPY_DEST

		declare -a SAVE
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
		cd $PREBUILT_DIR
		git add -A .
		git commit -a \
			-m "Travis build #$TRAVIS_BUILD_NUMBER of $GIT_REVISION for PLATFORM=$PLATFORM TARGET=$TARGET CPU=$CPU" \
			-m "" \
			-m "From https://github.com/$TRAVIS_REPO_SLUG/tree/$TRAVIS_COMMIT" \
			-m "$TRAVIS_COMIT_MESSAGE"
		git diff HEAD~1 --stat=1000,1000
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
		echo "- make clean ($PLATFORM $TARGET)"
		echo "---------------------------------------------"
		make clean || return 1
		echo "============================================="

		# Check that make clean didn't leave anything behind
		find | sort | grep -v "__pycache__" > /tmp/filelist.after
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
			return 1
		fi
	fi
	return 0
}

declare -a SUCCESSES
declare -a FAILURES


# Clone prebuilt repo to copy results into
if [ ! -z "$TRAVIS_PULL_REQUEST" -a "$TRAVIS_PULL_REQUEST" != "false" ]; then
	# Don't do prebuilt for a pull request.
	echo ""
	echo ""
	echo ""
	echo "- Pull request, so no prebuilt pushing."
elif [ -z "$GH_TOKEN" ]; then
	# Only if run by travis display error
	if [ ! -z $TRAVIS_BUILD_NUMBER  ]; then
		echo ""
		echo ""
		echo ""
		echo "- No Github token so unable to copy built files"
	fi
elif [ -z "$TRAVIS_BRANCH" ]; then
	echo ""
	echo ""
	echo ""
	echo "- No branch name, unable to copy built files"
else
	# Look at repo we are running in to determine where to try pushing to if in a fork
	PREBUILT_REPO=HDMI2USB-firmware-prebuilt
	PREBUILT_REPO_OWNER=$(echo $TRAVIS_REPO_SLUG|awk -F'/' '{print $1}')
	GIT_REVISION=$TRAVIS_BRANCH/$(git describe)
	ORIG_COMMITTER_NAME=$(git log -1 --pretty=%an)
	ORIG_COMMITTER_EMAIL=$(git log -1 --pretty=%ae)
	echo ""
	echo ""
	echo ""
	echo "- Uploading built files to github.com/$PREBUILT_REPO_OWNER/$PREBUILT_REPO"
	echo "---------------------------------------------"
	export PREBUILT_DIR="/tmp/HDMI2USB-firmware-prebuilt"
	(
		# Do a sparse, shallow checkout to keep disk space usage down.
		mkdir -p $PREBUILT_DIR
		cd $PREBUILT_DIR
		git init > /dev/null
		git config core.sparseCheckout true
		git remote add origin https://$GH_TOKEN@github.com/$PREBUILT_REPO_OWNER/${PREBUILT_REPO}.git
		cat > .git/info/sparse-checkout <<EOF
*.md
archive/*
archive/*/*
!archive/*/*/*
archive/**/sha256sum.txt
**/stable
**/testing
**/unstable
EOF
		git fetch --depth 1 origin master
		git checkout master
		echo ""
		PREBUILT_DIR_DU=$(du -h -s . | sed -e's/[ \t]*\.$//')
		echo "Prebuilt repo checkout is using $PREBUILT_DIR_DU"
	)
	echo "============================================="
fi

if [ -z "$CPUS" ]; then
	if [ -z "$CPU" ]; then
		#CPUS="lm32 or1k riscv32"
		CPUS="lm32 or1k"
	else
		CPUS="$CPU"
	fi
fi

START_TARGET="$TARGET"
START_TARGETS="$TARGETS"
for PLATFORM in $PLATFORMS; do
	if [ -z "$START_TARGETS" ]; then
		if [ -z "$SKIP_TARGETS" ]; then
			SKIP_TARGETS="__"
		fi
		if [ ! -z "$START_TARGETS" ]; then
			TARGETS="$START_TARGETS"
		elif [ ! -z "$START_TARGET" ]; then
			TARGETS="$START_TARGET"
		else
			TARGETS=$(ls targets/${PLATFORM}/*.py | grep -v "__" | grep -v "$SKIP_TARGETS" | sed -e"s+targets/${PLATFORM}/++" -e"s/.py//")
		fi
	fi

	echo ""
	echo ""
	echo ""
	echo "Running with TARGETS='$TARGETS'"
	for TARGET in $TARGETS; do
		for CPU in $CPUS; do
			build $PLATFORM $TARGET $CPU && :
			RETURN=$?
			if [ "$RETURN" -eq 0 ]; then
				SUCCESSES+=("$PLATFORM+$TARGET+$CPU")
			else
				FAILURES+=("$PLATFORM+$TARGET+$CPU")
			fi
		done
	done
done

if [ ! -z "$PREBUILT_DIR" ]; then
	echo ""
	echo ""
	echo ""
	echo "Pushing prebuilt binaries"
	echo "============================================="
	(
	cd $PREBUILT_DIR
	for i in 1 2 3 4 5 6 7 8 9 10; do	# Try 10 times.
		if [ "$TRAVIS_BRANCH" = "master" ]; then
			echo "Pushing with PLATFORMS='$PLATFORMS'"
			echo
			for PLATFORM in $PLATFORMS; do
				(
				if [ ! -d "$PLATFORM/firmware" ]; then
					echo "No firmware directory for $PLATFORM, skipping."
					continue
				fi
				echo
				echo "Updating unstable link (Try $i)"
				echo "---------------------------------------------"
				cd $PLATFORM/firmware
				LATEST="$(ls ../../archive/master/ | sort -V | tail -n 1)"
				echo "Latest firmware is $LATEST (current is $(readlink unstable))"
				HDMI2USB_FIRMWARE="../../archive/master/$LATEST/$PLATFORM/hdmi2usb/lm32"
				echo "Checking for '$HDMI2USB_FIRMWARE'"
				if [ -d "$HDMI2USB_FIRMWARE" -a "$(readlink unstable)" != "$HDMI2USB_FIRMWARE" ]; then
					echo "Changing $PLATFORM from '$(readlink unstable)' to '$HDMI2USB_FIRMWARE'"
					ln -sfT "$HDMI2USB_FIRMWARE" unstable
					git add unstable
					git commit -a \
						-m "Updating unstable link (Travis build #$TRAVIS_BUILD_NUMBER of $GIT_REVISION for PLATFORM=$PLATFORM TARGET=$TARGET CPU=$CPU)" \
						-m "" \
						-m "From https://github.com/$TRAVIS_REPO_SLUG/tree/$TRAVIS_COMMIT" \
						-m "$TRAVIS_COMMIT_MESSAGE"
				else
					echo "Not updating $PLATFORM"
				fi
				)
			done
		else
			echo "Not updating link as on branch '$TRAVIS_BRANCH'"
		fi
		echo
		echo "Merging (Try $i)"
		echo "---------------------------------------------"
		git fetch
		git merge origin/master --stat --commit -m "Merging #$TRAVIS_JOB_NUMBER of $GIT_REVISION"
		echo
		echo "Changes to be pushed (Try $i)"
		echo "---------------------------------------------"
		git diff origin/master --stat=1000,1000
		git diff origin/master --quiet --exit-code && break
		echo
		echo "Pushing (Try $i)"
		echo "---------------------------------------------"
		if git push --quiet origin master > /dev/null 2>&1 ; then
			echo "Push success!"
		else
			echo "Push failed :-("
		fi
	done
	echo
	echo "Push finished!"
	)
fi

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

