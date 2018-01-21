#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SCRIPT_SRC=$(realpath ${BASH_SOURCE[0]})
SCRIPT_DIR=$(dirname $SCRIPT_SRC)

if [ $SOURCED = 1 ]; then
        echo "You must run this script, rather then try to source it."
        echo "$SETUP_SRC"
        return
fi

FIRMWARE_DIR=$SCRIPT_DIR

X=$1

set -e

# These must be outside the heredoc below otherwise the script won't error.
TMPFILE_H=$(tempfile -s .h 2>/dev/null || mktemp --suffix=.h)
TMPFILE_C=$(tempfile -s .c 2>/dev/null || mktemp --suffix=.c)

cat $FIRMWARE_DIR/hdmi_in0.h | sed \
	-e"s/IN0_INDEX\([^0-9]\+\)0/IN${X}_INDEX\1$X/g" \
	-e"s/IN0/IN$X/g" \
	-e"s/in0/in$X/g" \
	-e"s/dvisampler0/dvisampler$X/g" \
	> $TMPFILE_H

cat $FIRMWARE_DIR/hdmi_in0.c | sed \
	-e"s/IN0/IN$X/g" \
	-e"s/in0/in$X/g" \
	-e"s/dvisampler0/dvisampler$X/g" \
	> $TMPFILE_C

if ! cmp -s $TMPFILE_H hdmi_in$X.h; then
	echo "Updating hdmi_in$X.h"
	mv $TMPFILE_H hdmi_in$X.h
fi

if ! cmp -s $TMPFILE_C hdmi_in$X.c; then
	echo "Updating hdmi_in$X.c"
	mv $TMPFILE_C hdmi_in$X.c
fi
