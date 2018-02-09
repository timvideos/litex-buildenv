#!/bin/bash

function prebuilt() {
	export FULL_PLATFORM=$1
	export TARGET=$2
	export FULL_CPU=$3

	if [ x"$4" != x"" ]; then
		FIRMWARE=$4
	else
		unset $FIRMWARE
	fi
	export FIRMWARE
	.travis/generate-prebuilt-list.py || return 1
	return 0
}

if [ x"$TRAVIS_BRANCH" = x"master" ]; then
	echo ""
	echo ""
	echo ""
	echo "Updating prebuilt binaries"
	echo "============================================="
	for i in 1 2 3 4 5 6 7 8 9 10; do	# Try 10 times.
		export FUNC=prebuilt

		. .travis/run.inc.sh && :
		FAILED=$?

		if [ $FAILED -eq 0 ]; then
			echo "Update succeed!"
			break
		else
			echo "Update failed!"
		fi
	done
	echo
	echo "Push finished!"
fi
