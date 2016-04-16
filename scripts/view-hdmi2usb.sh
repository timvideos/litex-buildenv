#!/bin/sh

I=0
while true; do
	echo
	if ! v4l-info /dev/video$I > /dev/null 2>&1; then
		echo "No /dev/video$I"
		break
	else
		echo "/dev/video$I - exists!"
	fi

	if v4l-info /dev/video$I | grep 'HDMI2USB' > /dev/null 2>&1; then
		echo "Device /dev/video$I *is* a HDMI2USB"
		export HDMI2USB=/dev/video$I
		break
 	else
		echo "Device /dev/video$I is *not* a HDMI2USB"
	fi

 	I=$((I+1))
done

WIDTH=1024
HEIGHT=768

mplayer tv:// -tv driver=v4l2:width=$WIDTH:height=$HEIGHT:device=$HDMI2USB -vf screenshot -vo xv
#guvcview --device=$HDMI2USB --show_fps=1 --size=$WIDTHx$HEIGHT
