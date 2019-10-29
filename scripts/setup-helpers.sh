function verify_system {
	if [ ! -z "$HDMI2USB_ENV" ]; then
		echo "Already sourced this file."
		return 1
	fi

	if [ ! -z "$SETTINGS_FILE" -o ! -z "$XILINX" ]; then
		echo "You appear to have sourced the Xilinx ISE settings, these are incompatible with building."
		echo "Please exit this terminal and run again from a clean shell."
		return 1
	fi

	# Conda does not support ' ' in the path (it bails early).
	if echo "${SETUP_DIR}" | grep -q ' '; then
		echo "You appear to have whitespace characters in the path to this script."
		echo "Please move this repository to another path that does not contain whitespace."
		return 1
	fi

	# Conda does not support ':' in the path (it fails to install python).
	if echo "${SETUP_DIR}" | grep -q ':'; then
		echo "You appear to have ':' characters in the path to this script."
		echo "Please move this repository to another path that does not contain this character."
		return 1
	fi

	# Check ixo-usb-jtag *isn't* installed
	if [ -e /lib/udev/rules.d/85-ixo-usb-jtag.rules ]; then
		echo "Please uninstall ixo-usb-jtag package from the timvideos PPA, the"
		echo "required firmware is included in the HDMI2USB modeswitch tool."
		echo
		echo "On Debian/Ubuntu run:"
		echo "  sudo apt-get remove ixo-usb-jtag"
		echo
		return 1
	fi

	if [ -f /etc/udev/rules.d/99-hdmi2usb-permissions.rules -o -f /lib/udev/rules.d/99-hdmi2usb-permissions.rules -o -f /lib/udev/rules.d/60-hdmi2usb-udev.rules -o ! -z "$HDMI2USB_UDEV_IGNORE" ]; then
		true
	else
		echo "Please install the HDMI2USB udev rules."
		echo "These are installed by scripts/download-env-root.sh"
		echo
		return 1
	fi
}

function fix_conda {
	for CONDA_SITE_PACKAGES in $(realpath $CONDA_DIR/lib/python*/site-packages/); do
		CONDA_COMMON_PATH="$CONDA_SITE_PACKAGES/conda/common/path.py"
		if [ ! -e $CONDA_COMMON_PATH ]; then
			continue
		fi
		if grep -q "def expanduser" $CONDA_COMMON_PATH; then
			echo "In $CONDA_SITE_PACKAGES conda/common/path.py is already patched."
			continue
		fi
		START_SUM=$(sha256sum $CONDA_COMMON_PATH | sed -e's/ .*//')
		(echo -n "In $CONDA_SITE_PACKAGES " && cd $CONDA_SITE_PACKAGES && patch -p1 || exit 1) <<EOF
diff --git a/conda/common/path.py b/conda/common/path.py
index 0228a3d0b..ffb879a39 100644
--- a/conda/common/path.py
+++ b/conda/common/path.py
@@ -42,6 +42,10 @@ def is_path(value):
     return re.match(PATH_MATCH_REGEX, value)
 
 
+def expanduser(path):
+    return expandvars(path.replace('~', '${CONDA_DIR}'))
+
+
 def expand(path):
     # if on_win and PY2:
     #     path = ensure_fs_path_encoding(path)

EOF
		END_SUM=$(sha256sum $CONDA_COMMON_PATH | sed -e's/ .*//')
		if [ $START_SUM != $END_SUM ]; then
			sed -i -e"s/$START_SUM/$END_SUM/" $(find $CONDA_DIR -name paths.json)
		else
			echo "Unable to patch conda path module!"
			return 1
		fi
	done
}

function pin_conda_package {
	CONDA_PACKAGE_NAME=$1
	CONDA_PACKAGE_VERSION=$2
	echo "Pinning ${CONDA_PACKAGE_NAME} to ${CONDA_PACKAGE_VERSION}"
	CONDA_PIN_FILE=$CONDA_DIR/conda-meta/pinned
	CONDA_PIN_TMP=$CONDA_DIR/conda-meta/pinned.tmp
	touch ${CONDA_PIN_FILE}
	cat ${CONDA_PIN_FILE} | grep -v ${CONDA_PACKAGE_NAME} > ${CONDA_PIN_TMP} || true
	echo "${CONDA_PACKAGE_NAME} ==${CONDA_PACKAGE_VERSION}" >> ${CONDA_PIN_TMP}
	cat ${CONDA_PIN_TMP} | sort > ${CONDA_PIN_FILE}
}

function install_conda {
	echo
	echo "Installing conda (self contained Python environment with binary package support)"
	if [[ ! -e $CONDA_DIR/bin/conda ]]; then
		cd $BUILD_DIR
		# FIXME: Get the miniconda people to add a "self check" mode
		wget --no-verbose --continue https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
		#wget --continue https://repo.anaconda.com/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh -O Miniconda3-latest-Linux-x86_64.sh
		chmod a+x Miniconda3-latest-Linux-x86_64.sh
		# -p to specify the install location
		# -b to enable batch mode (no prompts)
		# -f to not return an error if the location specified by -p already exists
		(
			export HOME=$CONDA_DIR
			./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b -f || exit 1
		)
		fix_conda
		conda config --system --add envs_dirs $CONDA_DIR/envs
		conda config --system --add pkgs_dirs $CONDA_DIR/pkgs
	fi
	conda config --system --set always_yes yes
	conda config --system --set changeps1 no
	pin_conda_package conda ${CONDA_VERSION}
	conda update -q conda
	fix_conda
	conda config --system --add channels timvideos
	conda info
}

function check_import {
	MODULE=$1
	if python3 -c "import $MODULE"; then
		echo "$MODULE found"
		return 0
	else
		echo "$MODULE *NOT* found!"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

function check_import_version {
	MODULE=$1
	EXPECT_VERSION=$2
	ACTUAL_VERSION=$(python3 -c "import $MODULE; print($MODULE.__version__)")
	if echo "$ACTUAL_VERSION" | grep -q $EXPECT_VERSION > /dev/null; then
		echo "$MODULE found at $ACTUAL_VERSION"
		return 0
	else
		echo "$MODULE (version $EXPECT_VERSION) *NOT* found!"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

function check_exists {
	TOOL=$1
	if which $TOOL >/dev/null; then
		echo "$TOOL found at $(which $TOOL)"
		return 0
	else
		echo "$TOOL *NOT* found"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

function check_version {
	TOOL=$1
	VERSION=$2
	if $TOOL --version 2>&1 | grep -q $VERSION > /dev/null; then
		echo "$TOOL found at $VERSION"
		return 0
	else
		$TOOL --version
		echo "$TOOL (version $VERSION) *NOT* found"
		echo "Please try running the $SETUP_DIR/download-env.sh script again."
		return 1
	fi
}

