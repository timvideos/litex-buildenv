#!/bin/bash

SCRIPT_SRC=$(realpath ${BASH_SOURCE[0]})
SCRIPT_DIR=$(dirname $SCRIPT_SRC)
TOP_DIR=$(realpath $SCRIPT_DIR/..)
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
	echo "You must run this script, rather then try to source it."
	echo "$SCRIPT_SRC"
	exit 1
fi

source $SCRIPT_DIR/build-common.sh

init

case $CPU in
	vexriscv)
    		CPU_TYPE="VexRiscv"
		;;
	picorv32)
    		CPU_TYPE="PicoRV32"
		;;
	*)
		echo "Simulating the current configuration is not supported in Renode yet - skipping the test"
		exit 0
		;;
esac

if [ "$PLATFORM" == "mimas_a7" ] || [ "$PLATFORM" == "netv2" ] || [ "$PLATFORM" == "pano_logic_g2" ]; then
    # the test load binaries into the flash to avoid using netboot on CI server
    echo "$PLATFORM platform does not have flash memory - skipping the test"
    exit 0
fi

if [ "$PLATFORM" == "ice40_hx8k_b_evn" ] || [ "$PLATFORM" == "tinyfpga_bx" ] || [ "$PLATFORM" == "icefun" ]; then
    # TODO: remove after this is handled in Renode
    echo "$PLATFORM has memory regions of size currently not supported in Renode - skipping the test"
    exit 0
fi

if [ "$FIRMWARE" == "zephyr" ]; then
    if [ "$PLATFORM" == "icebreaker" ]; then
        # running Zephyr firmware directly from flash is not supported at the moment
        # as it requires to enable XIP and include flash section in the DTS;
        # TODO: add this in the future
        echo "Running $FIRMWARE directly from flash is currently not supported - skipping the test"
        exit 0
    fi
fi

# Download prebuilt renode Release with new terminal tester support
conda install -c antmicro/label/test -c conda-forge renode=v1.8.2_with_new_terminal_tester
RENODE_BIN=$CONDA_PREFIX/bin/renode

LITEX_CONFIG_FILE="$TARGET_BUILD_DIR/test/csr.csv"
if [ ! -f "$LITEX_CONFIG_FILE" ]; then
	make firmware
fi

RENODE_SCRIPTS_DIR="$TOP_DIR/$TARGET_BUILD_DIR/renode"
RENODE_RESC="$RENODE_SCRIPTS_DIR/litex_buildenv.resc"
RENODE_REPL="$RENODE_SCRIPTS_DIR/litex_buildenv.repl"

mkdir -p $RENODE_SCRIPTS_DIR

if [ "$FIRMWARE" == "linux" ]; then
	# TODO: remove after this is handled in Renode
	echo "Running Linux tests is currently not supported - skipping the test"
	exit 0
else
	python $TOP_DIR/third_party/litex-renode/generate-renode-scripts.py $LITEX_CONFIG_FILE \
		--repl "$RENODE_REPL" \
		--resc "$RENODE_RESC" \
		--bios-binary "$TOP_DIR/$TARGET_BUILD_DIR/software/bios/bios.bin" \
		--firmware-binary "$TOP_DIR/$TARGET_BUILD_DIR/software/$FIRMWARE/firmware.bin"
fi

OPT_RENODE_LOCATION=$TOP_DIR/build/conda/opt/renode
TESTS_LOCATION=$TOP_DIR/tests/renode

cd $OPT_RENODE_LOCATION

if [ "$FIRMWARE" == "stub" ]; then
	# do not test the stub firmware
	python tests/run_tests.py \
		--variable LITEX_SCRIPT:"$RENODE_RESC" \
		--variable CPU_TYPE:"$CPU_TYPE" \
		--robot-framework-remote-server-full-directory $OPT_RENODE_LOCATION/bin \
		$TESTS_LOCATION/BIOS.robot \
		|| FAILED=1
else
	python tests/run_tests.py \
		--variable LITEX_SCRIPT:"$RENODE_RESC" \
		--variable CPU_TYPE:"$CPU_TYPE" \
		--robot-framework-remote-server-full-directory $OPT_RENODE_LOCATION/bin \
		$TESTS_LOCATION/BIOS.robot \
		$TESTS_LOCATION/Firmware-$FIRMWARE.robot \
		|| FAILED=1
fi

if [ "$FAILED" == "1" ]; then
	echo "+++ output +++"
	cat tests/tests/robot_output.xml
	exit 1
fi

