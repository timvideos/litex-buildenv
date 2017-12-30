#!/bin/bash

if [ "`whoami`" = "root" ]
then
    echo "Running the script as root is not permitted"
    exit 1
fi

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC="$(realpath ${BASH_SOURCE[0]})"
SETUP_DIR="$(dirname "${SETUP_SRC}")"
TOP_DIR="$(realpath "${SETUP_DIR}/..")"

if [ $SOURCED = 1 ]; then
	echo "You must run this script, rather then try to source it."
	echo "$SETUP_SRC"
	return
fi

set -euf
cd $TOP_DIR/firmware

find . '(' -name '*.c' -o -name '*.h' ')' \
| while read fn; do
	case $fn in
		./telnet.c)
			continue
			;;
	esac
	if grep -qF '\r\n' $fn; then
		echo "$fn" 'contains a \\r\\n.'
		echo 'You should just write \\n, stdio_wrap will transform this to a \\r\\n, as appropriate'
		exit 1
	fi
done
