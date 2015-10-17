#!/bin/bash -e

DEVS=$(lsusb|grep -E '(2a19|16c0|04b4|1d50|fb9a|1443)' |sed 's/:.*//;s/Bus //;s/Device //;s/ /\//')

if [ -z "$1" ]; then
    echo "$0: usage: $0 <file>"
    exit 1;
fi

for dev in $DEVS;do
    echo "Downloading $1 to $dev"
    /sbin/fxload -D /dev/bus/usb/$dev -t fx2lp -I $1
done

exit 0
