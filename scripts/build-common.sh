function init {
    if [ "`whoami`" = "root" ]
    then
        echo "Running the script as root is not permitted"
        exit 1
    fi

    if [ -z "$HDMI2USB_ENV" ]; then
        echo "You appear to not be inside the HDMI2USB environment."
        echo "Please enter environment with:"
        echo "  source scripts/enter-env.sh"
        exit 1
    fi

    # Imports TARGET, PLATFORM, CPU and TARGET_BUILD_DIR from Makefile
    eval $(make env)
    make info

    source $SCRIPT_DIR/settings.sh

    set -x
    set -e
}

function configure_tap {

	# Make the /dev/net exists, otherwise /dev/net/tun or /dev/net/tap0
	# can't exist.
	if [ ! -e /dev/net ]; then
		sudo true
		sudo mkdir /dev/net
	fi

	# Make the tun dev node exists
	if [ ! -e /dev/net/tun ]; then
		sudo true
		sudo modprobe tun
		if [ ! -e /dev/net/tun ]; then
			sudo mknod /dev/net/tun c 10 200
			sudo chown $(whoami) /dev/net/tun
		fi
	fi

	# Make the tap0 dev node exists
	if [ ! -e /dev/net/tap0 ]; then
		sudo true
		sudo mknod /dev/net/tap0 c 10 200
		sudo chown $(whoami) /dev/net/tap0
	fi

	# Check that the tap0 network interface exists
	if [ ! -e /sys/class/net/tap0 ]; then
		sudo true
		if sudo which openvpn > /dev/null; then
			sudo openvpn --mktun --dev tap0 --user $(whoami)
		elif sudo which tunctl > /dev/null; then
			sudo tunctl -t tap0 -u $(whoami)
		else
			echo "Unable to find tool to create tap0 device!"
			exit 1
		fi
	fi

	# Check the tap0 device if configure and up
	if sudo which ifconfig > /dev/null; then
		if ! ifconfig tap0 | grep -q "UP" || ! ifconfig tap0 | grep -q "$TFTP_IPRANGE.100"; then
			sudo true
			sudo ifconfig tap0 $TFTP_IPRANGE.100 netmask 255.255.255.0 up
		fi
	elif sudo which ip > /dev/null; then
		if ! ip addr show tap0 | grep -q "UP" || ! ip addr show tap0 | grep -q "$TFTP_IPRANGE.100"; then
			sudo true
			sudo ip addr add $TFTP_IPRANGE.100/24 dev tap0
			sudo ip link set dev tap0 up
		fi
	else
		echo "Unable to find tool to configure tap0 address"
		exit 1
	fi
}

function start_tftp {
	# Restart tftpd
	make tftpd_stop
	make tftpd_start
}

function parse_generated_header {
	# $1 - filename
	# $2 - define name

	grep $2 $TARGET_BUILD_DIR/software/include/generated/$1 | tr -s ' ' | cut -d' ' -f3
}

