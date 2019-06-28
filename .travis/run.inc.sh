if [ -z "$PLATFORMS" ]; then
	if [ -z "$SKIP_PLATFORMS" ]; then
		SKIP_PLATFORMS="sim"
	fi
	if [ -z "$PLATFORM" ]; then
		PLATFORMS=$(ls targets/ | grep -v ".py" | grep -v "common" | grep -v "$SKIP_PLATFORMS" | sed -e"s+targets/++")
	else
		PLATFORMS="$PLATFORM"
		unset PLATFORM
	fi
fi
echo "Running with PLATFORMS='$PLATFORMS'"

if [ -z "$CPUS" ]; then
	if [ -z "$CPU" ]; then
		CPUS="lm32 mor1kx picorv32 vexriscv"
	else
		CPUS="$CPU"
		unset CPU
	fi
fi

declare -a SUCCESSES
declare -a FAILURES

START_TARGET="$TARGET"
START_TARGETS="$TARGETS"
for FULL_PLATFORM in $PLATFORMS; do
	if [ -z "$START_TARGETS" ]; then
		if [ -z "$SKIP_TARGETS" ]; then
			SKIP_TARGETS="__"
		fi
		if [ ! -z "$START_TARGETS" ]; then
			TARGETS="$START_TARGETS"
		elif [ ! -z "$START_TARGET" ]; then
			TARGETS="$START_TARGET"
		else
			TARGETS=$(ls targets/${FULL_PLATFORM}/*.py | grep -v "__" | grep -v "$SKIP_TARGETS" | sed -e"s+targets/${FULL_PLATFORM}/++" -e"s/.py//")
		fi
	fi

	echo ""
	echo ""
	echo ""
	echo "Running with TARGETS='$TARGETS'"
	for TARGET in $TARGETS; do
		echo "Running with CPUS='$CPUS'"
		for FULL_CPU in $CPUS; do
			$FUNC $FULL_PLATFORM $TARGET $FULL_CPU $FIRMWARE && :
			RETURN=$?
			if [ "$RETURN" -eq 0 ]; then
				SUCCESSES+=("$FULL_PLATFORM+$TARGET+$FULL_CPU+$FIRMWARE")
			else
				FAILURES+=("$FULL_PLATFORM+$TARGET+$FULL_CPU+$FIRMWARE")
			fi
		done
	done
done
