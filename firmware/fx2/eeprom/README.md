# Flashing HDMI2USB VID:PID into Atlys board

A brand new Atlys Board gets listed by `lsusb` as *Digilent Development board
JTAG* with VID:PID as 1443:0007 We want to flash the EEPROM onboard the Atlys,
so that on powering up, it always shows up as *OpenMoko Device, TimVideos'
HDMI2USB (FX2) - Unconfigured device* with VID:PID as `1D50:60B5`.

https://github.com/timvideos/HDMI2USB/wiki/USB-IDs

## Steps:

* Obtain a copy of flcli from libfpgalink, and place it in your path

* Now use this command to flash the Atlys' EEPROM

  `sudo ./flcli -v 1D50:60B5 -i 1443:0007 --eeprom=eeprom/hdmi2usb_unconfigured_device.iic`

Thats it!! You have flashed your Atlys to appear as different device. Power
cycle the board and use `lsusb` to confirm.
