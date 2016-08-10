# Building HDMI2USB-misoc-firmware

These scripts are designed to bootstrap a firmware build environment on Ubuntu
14.04 LTS and also works on 16.04 though with less testing.

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


  * Ensure you have a free WebPACK license for ISE installed, see [http://www.xilinx.com/getlicense], ensure installed into ```~/.Xilinx/Xilinx.lic```

  * Ensure licence is activated by checking ISE:
  ```
  source /opt/Xilinx/14.7/ISE_DS/settings64.sh
  ise
  ```
  Go to About > Licence, ensure under "information" you can see your ISE WebPACK licence.
 
## Bootstrap
 
Run the bootstrap script to build an environment required for flashing
firmware:
```
curl -fsS https://raw.githubusercontent.com/timvideos/HDMI2USB-misoc-firmware/master/scripts/bootstrap.sh | bash
```

This clones the HDMI2USB-misoc-firmware repository, adds the timvideos
fpga-support PPA, installs packages required then downloads misoc and its
dependencies. Depending on your connection speed this could take a while to
download.

## Working with the firmware

### 1) Enter the environment

Before being able to run any of the build steps you must first `enter` the
development environment.

Before entering, you should set the type of board you want to use.  This is
done by doing;
```
export BOARD=opsis
```

To do this do the following steps;
```
cd HDMI2USB-misoc-firmware
source scripts/enter-env.sh
```

Once you source the environment your prompt should change to look something
like;
```
(H2U BOARD=opsis) #
```

FIXME: Add a `make test-env` which verifies the environment is working
(excpecially that the Xilinx stuff has a proper license stuff).

### 2) Build the gateware

Once you have entered the environment, you can build things.

Building the full HDMI2USB gateware takes roughly between 15 minutes and 30
minutes on a modern fast machine.

```
make gateware
```

At the end of running the build command, you should end up with;
```
Creating bit map...
Saving bit stream in "opsis_hdmi2usb-hdmi2usbsoc-opsis.bit".
Saving bit stream in "opsis_hdmi2usb-hdmi2usbsoc-opsis.bin".
Bitstream generation is complete.
Firmware 56008 bytes (9528 bytes left)
```

The built gateware will be in build/misoc/build/.

### 3) Configure your board

Before loading onto your board, you need to ensure that your board is in the
correct state.

---

#### Configuring the Opsis

To use the Opsis, you need to set the jumpers correctly, connect cables
correctly and then put the board into JTAG mode.

FIXME: Put something here about the Opsis.

##### Jumpers Configuration

The jumpers as set on the Opsis when it ships work.

FIXME: Put picture showing correct jumper configuration.

##### Cables

The programming computer must be connected to the USB-B port.

##### JTAG mode

By default the Opsis will boot into HDMI2USB mode. To load gateware onto the
board it must be switched into JTAG mode.

FIXME: Add instructions for switching the Opsis into JTAG mode.

 - [HDMI2USB-mode-switch](https://github.com/timvideos/HDMI2USB-mode-switch)
   then run:
   ```
   hdmi2usb-mode-switch --mode=jtag
   ```

 - Connect to console and use fx2 switch command.

---

#### Configuring the Atlys

Before loading the gateware you need to set the jumpers correctly and connect
the cables correctly.

FIXME: Put something here about the Atlys.

##### Jumpers Configuration

As the HDMI2USB firmware manipulates the EDID information the following jumpers
must be removed;

```
JP2/SDA (which connects the EDID lines from J1/HDMI IN to JA/HDMI OUT).
JP6 and JP7 (which connects the EDID lines from J3/HDMI IN to J2/HDMI OUT).
```

##### Cables

  * Plug board in using `PROG` port & switch on. If using a VM, ensure the
    device is passed through.

  * The other UART port is for the controlling the firmware. Recommend plugging
   :w
his in too so you can use/test the device.

---

### 4) Loading temporarily

You can load gateware and firmware onto your device temporarily for testing. If
you power cycle the device after this step it will go back to the state before
this step.

Load the gateware and firmware - see [1] if using a VM:
```
make load-gateware
```

On the Opsis, while loading the Blue LED (D1 / Done) and Green LED (D2) will
light up. After it has finished, both LED will turn off.

The output will look like this;
```
jtagspi_program
Info : usb blaster interface using libftdi
Info : This adapter doesn't support configurable speed
Info : JTAG tap: xc6s.tap tap/device found: 0x44028093 (mfg: 0x049 (Xilinx), part: 0x4028, ver: 0x4)
loaded file build/opsis_hdmi2usb-hdmi2usbsoc-opsis.bit to pld device 0 in 31s 983152us
```

Load fx2 firmware to enable USB capture:
```
make load-fx2
```

#### Common Errors

##### unable to open ftdi device

###### `device not found`

This error means that a HDMI2USB board in JTAG mode was not detected. Power cycle the board and make sure
you have followed the `3) Configure your board` section.

```
Warn : Adapter driver 'usb_blaster' did not declare which transports it allows; assuming legacy JTAG-only
Info : only one transport option; autoselect 'jtag'
Warn : incomplete ublast_vid_pid configuration
jtagspi_program
Info : usb blaster interface using libftdi
Error: unable to open ftdi device: device not found
```

###### `inappropriate permissions on device`

This error means that your user doesn't have permission to talk to the HDMI2USB
board. This is normally caused by not installing the udev rules which come
with HDMI2USB-mode-switch.

```
Warn : Adapter driver 'usb_blaster' did not declare which transports it allows; assuming legacy JTAG-only
Info : only one transport option; autoselect 'jtag'
Warn : incomplete ublast_vid_pid configuration
jtagspi_program
Info : usb blaster interface using libftdi
Error: unable to open ftdi device: inappropriate permissions on device!
```

##### Warn: Bypassing JTAG setup events due to errors

If you get an error like this;
```
Info : This adapter doesn't support configurable speed
Info : JTAG tap: xc6s.tap tap/device found: 0x03030303 (mfg: 0x181 (Solectron), part: 0x3030, ver: 0x0)
Warn : JTAG tap: xc6s.tap       UNEXPECTED: 0x03030303 (mfg: 0x181 (Solectron), part: 0x3030, ver: 0x0)
Error: JTAG tap: xc6s.tap expected 1 of 13: 0x04000093 (mfg: 0x049 (Xilinx), part: 0x4000, ver: 0x0)
Error: JTAG tap: xc6s.tap expected 2 of 13: 0x04001093 (mfg: 0x049 (Xilinx), part: 0x4001, ver: 0x0)
Error: JTAG tap: xc6s.tap expected 3 of 13: 0x04002093 (mfg: 0x049 (Xilinx), part: 0x4002, ver: 0x0)
Error: JTAG tap: xc6s.tap expected 4 of 13: 0x04004093 (mfg: 0x049 (Xilinx), part: 0x4004, ver: 0x0)
Error: JTAG tap: xc6s.tap expected 5 of 13: 0x04024093 (mfg: 0x049 (Xilinx), part: 0x4024, ver: 0x0)
```

It means the JTAG firmware on the FX2 has gotten confused. Use mode-switch tool
to switch to serial mode and then back to the jtag mode like this;
```
hdmi2usb-mode-switch --mode=serial
hdmi2usb-mode-switch --mode=jtag
```

### 5) Testing

Connect to lm32 softcore to send direct commands to the HDMI2USB such as
changing resolution:
```
make connect-lm32
```
Set a mode/capture - type 'help' and read instructions.

You likely need to enable a video mode, frame buffer & encoder.

'status' helps to see what the firmware is doing.

The following commands are an example of what is needed;
```
encoder on
encoder quality 85
video_matrix connect input1 output0
video_matrix connect input1 output1
video_matrix connect input1 encoder
```

View the video output on your computer with your preferred tool.

The scripts/view-hdmi2usb.sh script will try and find a suitable tool to display.
```
make view
# or
scripts/view-hdmi2usb.sh
```

### 6) Loading permanently

If you are happy with the firmware you can load it onto the board so that if
persists after power cycle.


```
make flash
```

#### Footnotes

  [1] If you are in a VM, during flashing the device will change USB UUID's up to 3 times.  You can just run the command above again until you see "Programming successful!" (you may need to choose the new USB vendor/device ID in your hypervisor to pass through).

  [2] Note firmware is only temporarily flashed to the device and is lost if HDMI2USB is power cycled, so has to be reflashed.  You can use the 'flash-hdmi2usb.sh' script metioned in step 9.

---

#### Files

  * bootstrap.sh: script to run on a fresh Ubuntu 14.04 LTS install
  * download-env.sh: called from bootstrap (gets and installs software)
  * download-env-root.sh: called from bootstrap and runs as root.
  * enter-env.sh: script to run after installation to enter environment

  * view-hdmi2usb.sh: test script to view HDMI2USB output



