#!/bin/bash

set -e

./.travis/prevent-condarc.sh

./.travis/fixup-git.sh

function setup() {
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

	DF_BEFORE_DOWNLOAD="$(($(stat -f --format="%a*%S" .)))"
	(
		echo ""
		echo "============================================="
		echo ""
		echo ""
		# Run the script once to check it works
		time scripts/download-env.sh || exit 1
		echo ""
		echo ""
		echo "============================================="
		echo ""
		echo ""
		# Run the script again to check it doesn't break things
		time scripts/download-env.sh || exit 1
		echo ""
		echo ""
		echo "============================================="

		echo ""
		echo ""
		echo ""
		echo "- Disk space free (after downloading environment)"
		echo "---------------------------------------------"
		df -h
		echo ""
		DF_AFTER_DOWNLOAD="$(($(stat -f --format="%a*%S" .)))"
		awk "BEGIN {printf \"Environment is using %.2f megabytes\n\",($DF_BEFORE_DOWNLOAD-$DF_AFTER_DOWNLOAD)/1024/1024}"

		echo "============================================="
		echo "============================================="
		echo ""
		echo ""
		set +x
		set +e
		source scripts/enter-env.sh || exit 1
	); return $?
}

export FUNC=setup
source .travis/run.inc.sh

echo ""
echo ""
echo ""
echo "The following setups succeeded"
echo "============================================="

for S in ${SUCCESSES[@]}; do
	echo $S | sed -e's/+/ /g'
done
echo ""
echo ""
echo ""
echo "The following setups failed!"
echo "============================================="

for F in ${FAILURES[@]}; do
	echo $F | sed -e's/+/ /g'
done

echo ""
echo ""
echo ""
echo "============================================="

if [ ${#FAILURES[@]} -ne 0 ]; then
	echo "One or more setups failed :("
	exit 1
else
	echo "All setups succeeded! \\o/"
fi

./.travis/download-prebuilt.sh
