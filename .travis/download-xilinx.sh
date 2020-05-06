# FIXME: Move this to a separate script!
# Cutback Xilinx ISE for CI
# --------
# Save the passphrase to a file so we don't echo it in the logs
if [ ! -z "$XILINX_PASSPHRASE" ]; then
	XILINX_PASSPHRASE_FILE=$(tempfile -s .passphrase | mktemp --suffix=.passphrase)
	trap "rm -f -- '$XILINX_PASSPHRASE_FILE'" EXIT
	echo $XILINX_PASSPHRASE >> $XILINX_PASSPHRASE_FILE

	# Need gpg to do the unencryption
	export XILINX_DIR=$BUILD_DIR/Xilinx
	export LIKELY_XILINX_LICENSE_DIR=$XILINX_DIR
	if [ ! -d "$XILINX_DIR" -o ! -d "$XILINX_DIR/opt" ]; then
		(
			cd $BUILD_DIR
			mkdir -p Xilinx
			cd Xilinx

			wget -q http://xilinx.timvideos.us/index.txt -O xilinx-details.txt
			XILINX_TAR_INFO=$(cat xilinx-details.txt | grep tar.bz2.gpg | tail -n 1)
			XILINX_TAR_FILE=$(echo $XILINX_TAR_INFO | sed -e's/[^ ]* //' -e's/.gpg$//')
			XILINX_TAR_MD5=$(echo $XILINX_TAR_INFO | sed -e's/ .*//')

			# This setup was taken from https://github.com/m-labs/artiq/blob/master/.travis/get-xilinx.sh
			wget --no-verbose -c http://xilinx.timvideos.us/${XILINX_TAR_FILE}.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 ${XILINX_TAR_FILE}.gpg
			tar -xjf $XILINX_TAR_FILE

			# Remove the tar file to free up space.
			rm ${XILINX_TAR_FILE}*

			# FIXME: Hacks to try and make Vivado work.
			mkdir -p $XILINX_DIR/opt/Xilinx/Vivado/2017.3/scripts/rt/data/svlog/sdbs
			mkdir -p $XILINX_DIR/opt/Xilinx/Vivado/2017.3/tps/lnx64/jre

			# Make ISE stop complaining about missing wbtc binary
			mkdir -p $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64
			ln -s /bin/true $XILINX_DIR/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/wbtc

			# Relocate ISE from /opt to $XILINX_DIR
			for i in $(grep -l -Rsn "/opt/Xilinx" $XILINX_DIR/opt)
			do
				sed -i -e "s!/opt/Xilinx!$XILINX_DIR/opt/Xilinx!g" $i
			done
			wget --no-verbose http://xilinx.timvideos.us/Xilinx.lic.gpg
			cat $XILINX_PASSPHRASE_FILE | gpg --batch --passphrase-fd 0 Xilinx.lic.gpg

			sudo modprobe dummy
			sudo ip link set name eth0 dev dummy0
			sudo ifconfig eth0 hw ether 08:00:27:68:c9:35
			#git clone https://github.com/mithro/impersonate_macaddress
			#cd impersonate_macaddress
			#make
		)
	fi
	rm $XILINX_PASSPHRASE_FILE
	trap - EXIT
fi
if [ -z "$LIKELY_XILINX_LICENSE_DIR" ]; then
	LIKELY_XILINX_LICENSE_DIR="$HOME/.Xilinx"
fi

XILINX_SETTINGS_ISE='/opt/Xilinx/*/ISE_DS/settings64.sh'
XILINX_SETTINGS_VIVADO='/opt/Xilinx/Vivado/*/settings64.sh'

if [ -z "$XILINX_DIR" ]; then
	LOCAL_XILINX_DIR=$BUILD_DIR/Xilinx
	if [ -d "$LOCAL_XILINX_DIR/opt/Xilinx/" ]; then
		# Reserved MAC address from documentation block, see
		# http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml
		export LIKELY_XILINX_LICENSE_DIR=$LOCAL_XILINX_DIR
		#export MACADDR=90:10:00:00:00:01
		export MACADDR=08:00:27:68:c9:35
		#export LD_PRELOAD=$XILINX_DIR/impersonate_macaddress/impersonate_macaddress.so
		#ls -l $LD_PRELOAD
		export XILINX_DIR=$LOCAL_XILINX_DIR
		export XILINX_LOCAL_USER_DATA=no
	fi
fi
if [ -z "$LIKELY_XILINX_LICENSE_DIR" ]; then
	LIKELY_XILINX_LICENSE_DIR="$HOME/.Xilinx"
fi
shopt -s nullglob
XILINX_SETTINGS_ISE=($XILINX_DIR/$XILINX_SETTINGS_ISE)
XILINX_SETTINGS_VIVADO=($XILINX_DIR/$XILINX_SETTINGS_VIVADO)
shopt -u nullglob

echo "        Xilinx directory is: $XILINX_DIR/opt/Xilinx/"
if [ ${#XILINX_SETTINGS_ISE[@]} -gt 0 ]; then
	echo -n "                             - Xilinx ISE toolchain found!"
	if [ ${#XILINX_SETTINGS_ISE[@]} -gt 1 ]; then
		echo -n " (${#XILINX_SETTINGS_ISE[@]} versions)"
	fi
	echo ""
	export HAVE_XILINX_ISE=1
else
	export HAVE_XILINX_ISE=0
fi
if [ ${#XILINX_SETTINGS_VIVADO[@]} -gt 0 ]; then
	echo -n "                             - Xilinx Vivado toolchain found!"
	if [ ${#XILINX_SETTINGS_VIVADO[@]} -gt 1 ]; then
		echo -n " (${#XILINX_SETTINGS_VIVADO[@]} versions)"
	fi
	echo ""
	export HAVE_XILINX_VIVADO=1
else
	export HAVE_XILINX_VIVADO=0
fi
if [ $HAVE_XILINX_ISE -eq 1 -o $HAVE_XILINX_VIVADO -eq 1 ]; then
	export HAVE_XILINX_TOOLCHAIN=1
else
	export HAVE_XILINX_TOOLCHAIN=0
fi

# Detect a likely lack of license early, but just warn if it's missing
# just in case they've set it up elsewhere.
if [ ! -e $LIKELY_XILINX_LICENSE_DIR/Xilinx.lic ]; then
	echo "(WARNING) Please ensure you have installed Xilinx and have a license."
	echo "(WARNING) Copy your Xilinx license to Xilinx.lic in $LIKELY_XILINX_LICENSE_DIR to suppress this warning."
else
	echo "          Xilinx license in: $LIKELY_XILINX_LICENSE_DIR"
	export XILINXD_LICENSE_FILE=$LIKELY_XILINX_LICENSE_DIR
fi
