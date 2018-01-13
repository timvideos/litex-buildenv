#!/bin/bash

set -e

./.travis/prevent-condarc.sh

./.travis/fixup-git.sh

function setup() {
	export FULL_PLATFORM=$1
	export TARGET=$2
	export FULL_CPU=$3

	if [ x$4 != x ]; then
		FIRMWARE=$4
	else
		unset $FIRMWARE
	fi

	if [ -z "$FULL_PLATFORM" -o -z "$TARGET" -o -z "$FULL_CPU" ]; then
		echo "usage: setup FULL_PLATFORM TARGET FULL_CPU FIRMWARE"
		echo "  got: setup '$FULL_PLATFORM' '$TARGET' '$FULL_CPU' '$FIRMWARE'"
		return 1
	fi

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
