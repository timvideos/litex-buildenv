#!/bin/sh

set -euf
cd "$(dirname "$0")"

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
