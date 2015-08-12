# Building HDMI2USB-misoc-firmware
#### (assumes a new Ubuntu Desktop 14.04 LTS install)

TODO: Complete this, clean this up, move some of it back into the script

These scripts are designed to bootstrap an environment on Ubuntu 14.04 LTS.

To get started (will install packages, etc):

  * Run the bootstrap script to get everything required for flashing firmware:
  ```curl -fsS https://raw.githubusercontent.com/timvideos/HDMI2USB-misoc-firmware/scripts/scripts/bootstrap.sh | bash```
  
  * Download & install Xilinx ISE WebPACK 14.7 into the default location in /opt/
  
  * Ensure you have a free WebPACK licence for ISE installed, see http://license.xilinx.com/getLicense
  
  * Ensure licence is activated by checking ISC:
  ```
  source /opt/Xilinx/14.7/ISE_DS/settings64.sh 
  isc
  ```
  Go to About > Licence, ensure under "information" you can see your ISC WebPACK licence.  
  
  * Change into the HDMI2USB-misoc-firmware directory:
  ```cd ~/HDMI2USB-misoc-firmware```
  
  * Initialise the environment:
  ```source scripts/setup-env.sh```  
  
  * Build the gateware:
  ```make gateware```
  This may fail at the end after it builds the gateware (as it will try to flash the gateware), this is OK, as long as the gateware files have been built:
  
```Saving bit stream in "atlys_hdmi2usb-hdmi2usbsoc-atlys.bit".
Saving bit stream in "atlys_hdmi2usb-hdmi2usbsoc-atlys.bin".
```
   The built gateware will be in build/misoc/build/.

  * Ensure board has the right pins set:
  
  As the HDMI2USB firmware manipulates the EDID information the following jumpers must be removed;

JP2/SDA (which connects the EDID lines from J1/HDMI IN to JA/HDMI OUT).
JP6 and JP7 (which connects the EDID lines from J3/HDMI IN to J2/HDMI OUT).
  
  * Plug board in using PROG port & switch on.  If using a VM, ensure the device is passed through.
  
  * Load in custom udev rules:
  (make a script, which is called as part of get-env)

```  
  cat > /etc/udev/rules.d/52-hdmi2usb.rules <<EOF
# Grant permission to makestuff usb devices.
ATTR{idVendor}=="1d50", MODE:="666"

# Grant permissions to hdmi2usb usb devices.
ATTR{idVendor}=="fb9a", MODE:="666"

# Grant permissions to unconfigured cypress chips.
ATTR{idVendor}=="04b4", MODE:="666"

# Grant permissions to Digilent Development board JTAG
ATTR{idVendor}=="1443", MODE:="666"
EOF
```
udevadm control --reload-rules
  
  * Flash the gateware and firmware - see [1] if using a VM:
  
  ```PROG=fpgalink make load-gateware```
  
  * Connect to lm32 softcore:
  ```make connect-lm32```
  
  * Set a mode/capture - press 'h' and read instructions. TODO: Explain this more

  * Run fx2 firmware to enable USB capture:
  
  ADD TO ENV GET:  sudo apt-get -y install sdcc fxload
  ```make load-fx2-firmware```
  
---

CHANGES TO GET ENV SCRIPT:

````
sudo apt-get -y install sdcc fxload
make load-fx2-firmware
````  

```
   cd the build directory
   git clone mithro/exar-uart-driver 
   cd exar-uart-driver
   sudo apt-get install linux-headers-generic debhelper module-assistant
   dpkg-buildpackage -rfakeroot
   sudo dpkg --install ../v blah (copy from README.Debian)
   (copy package build command from README.Debian)
```


add to misoc setup part of get-env:

```
cd build/misoc/tools
make
```

```
   sudo gpasswd -a <userid> dialout
```


  * Flash the fx firmware (shouldn't be required):
   
   ```make load-lm32-firmware```
   If this doesn't work the first time, try again.
  
---

To get a device working after above is all built (booted up, etc):
```
cd ~/HDMI2USB-misoc-firmware
source scripts/setup-env.sh
PROG=fpgalink make load-gateware
make load-lm32-firmware
```

#### Footnotes
  
  [1] If you are in a VM, during flashing the device will change USB UUID's up to 3 times.  You can just run the command above again until you see "Programming successful!" (you may need to choose the new USB vendor/device ID in your hypervisor to pass through).
  
---  

  * https://github.com/timvideos/HDMI2USB-firmware-prebuilt
  
  programmer i want to use when running make is
  fpgalink (probably)
  urjtag
  x3progs
  
  last two require firmware on device first, first will do firmware loading for me
  so probably use first
  
---

Files:

  * bootstrap.sh: script to run on a fresh Ubuntu 14.04 LTS install
  * get-env.sh: called from bootstrap (gets and installs software)
  * setup-env.sh: script to run after installation to setup environemnt 

