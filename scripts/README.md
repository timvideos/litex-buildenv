# Building HDMI2USB-misoc-firmware

These scripts are designed to bootstrap a firmware build environment on Ubuntu 14.04 LTS and also works on 15.04 though with less testing.

## Prerequisite

Install Xilinx ISE WebPACK 14.7 + activate a licence:

  * Download from [http://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/design-tools.html]
  * Install into the default location in /opt (requires X11 GUI):
  ```
  tar xvf Xilinx_ISE_DS_Lin_14.7_1015_1.tar
  cd Xilinx_ISE_DS_Lin_14.7_1015_1
  sudo ./xsetup
  ```
  Ensure you select "ISE WebPACK" 17403 MB


  * Ensure you have a free WebPACK license for ISE installed, see [http://license.xilinx.com/getLicense], ensure installed into ```~/.Xilinx/Xilinx.lic```

  * Ensure licence is activated by checking ISE:
  ```
  source /opt/Xilinx/14.7/ISE_DS/settings64.sh
  ise
  ```
  Go to About > Licence, ensure under "information" you can see your ISE WebPACK licence.
 
## Bootstrap
 
Run the bootstrap script to build an environment required for flashing firmware:
  ```
  curl -fsS https://raw.githubusercontent.com/timvideos/HDMI2USB-misoc-firmware/master/scripts/bootstrap.sh | bash
  ```

This clones the HDMI2USB-misoc-firmware repository, adds the timvideos fpga-support PPA, installs packages required then downloads misoc and its dependencies. Depending on your connection speed this could take a while to download.

## Building the firmware

1. Initalise the environment (required for any of the build/load steps below[2]):
  ```
  cd HDMI2USB-misoc-firmware
  source scripts/setup-env.sh
  ```

2.  Build the gateware:
  ```
  make gateware
  ```

  This may fail at the end after it builds the gateware (as it will try to flash the gateware), this is OK, as long as the gateware files have been built:

  ```
  Saving bit stream in "atlys_hdmi2usb-hdmi2usbsoc-atlys.bit".
  Saving bit stream in "atlys_hdmi2usb-hdmi2usbsoc-atlys.bin".
  ```

   The built gateware will be in build/misoc/build/.

3. You've now built the HDMI2USB firmware/gateware.  Ensure board has the right pins set before flashing anything, and plug it in:

  As the HDMI2USB firmware manipulates the EDID information the following jumpers must be removed;

  ```
  JP2/SDA (which connects the EDID lines from J1/HDMI IN to JA/HDMI OUT).
  JP6 and JP7 (which connects the EDID lines from J3/HDMI IN to J2/HDMI OUT).
  ```

  * Plug board in using USB PROG port & switch on.  If using a VM, ensure the device is passed through.
  * Other USB port is for the HDMI2USB capture.  Recommend plugging this in too so you can use/test the device.
 
4.  Flash the gateware and firmware - see [1] if using a VM:

  ```
  make load-gateware
  ```
  (may need to run several times)

5.  Load fx2 firmware to enable USB capture:
  ```
  make load-fx2 
  ```

6. Connect to lm32 softcore to send direct commands to the HDMI2USB such as changing resolution:
  ```
  make connect-lm32
  ```
  Set a mode/capture - type 'help' and read instructions.
  You likely need to enable a video mode, framebuffer & encoder.
  'status' helps to see what the firmware is doing.

```
encoder on
encoder quality 85
video_matrix connect input1 output0
video_matrix connect input1 output1
video_matrix connect input1 encoder
video_matrix connect pattern encoder

mplayer tv:// -tv driver=v4l2:device=/dev/video1
```
---

Once everything has been built, get HDMI2USB running again after a power cycle by running this script, possibly multiple times if errors first attempt (does non-build steps above):
   ```
   ~/HDMI2USB-misoc-firmware/scripts/flash-hdmi2usb.sh
   ```

#### Footnotes

  [1] If you are in a VM, during flashing the device will change USB UUID's up to 3 times.  You can just run the command above again until you see "Programming successful!" (you may need to choose the new USB vendor/device ID in your hypervisor to pass through).

  [2] Note firmware is only temporarily flashed to the device and is lost if HDMI2USB is power cycled, so has to be reflashed.  You can use the 'flash-hdmi2usb.sh' script metioned in step 9.

---

#### Files

  * bootstrap.sh: script to run on a fresh Ubuntu 14.04 LTS install
  * get-env.sh: called from bootstrap (gets and installs software)
  * setup-env.sh: script to run after installation to setup environemnt

  * 52-hdmi2usb.rules: udev rules loaded by get-env.sh
  * view-hdmi2usb.sh: test script to view HDMI2USB output
  * flash-hdmi2usb.sh: script to run after gateware/firmware built
