#!/bin/sh

if [ ! -d /dev/hdmi2usb ]; then
	I=0
	for DEV in $(ls /dev/video*); do
		echo
		if ! v4l-info $DEV > /dev/null 2>&1; then
			echo "No $DEV"
			break
		else
			echo "$DEV - exists!"
		fi

		if v4l-info $DEV | grep 'HDMI2USB' > /dev/null 2>&1; then
			echo "Device $DEV *is* a HDMI2USB"
			export HDMI2USB=$DEV
			break
		else
			echo "Device $DEV is *not* a HDMI2USB"
		fi
	done
else
	HDMI2USB=$(ls /dev/hdmi2usb/by-num/all*/video | head -n1)
fi

WIDTH=1280
HEIGHT=720

mplayer tv:// -tv driver=v4l2:width=$WIDTH:height=$HEIGHT:device=$HDMI2USB -vf screenshot -vo xv
#guvcview --device=$HDMI2USB --show_fps=1 --size=$WIDTHx$HEIGHT
