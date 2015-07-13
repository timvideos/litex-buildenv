# Cypress FX2 Firmware

This directory contains the FX2 firmware for the HDMI2USB project. It uses the
Open Source fx2lib, a free reimplementation of the Cypress support library.

The firmware is responsible for transporting the video data off of the FPGA. It
does this by enumerating as a USB Video Class device; a standard way of
interfacing devices such as webcams to a host. Linux, Windows and OS X all
include support out of the box for reading taking to such devices.

The firmware is also used for control and debugging of the system, through a
USB Communications Class Device. This is a common way of attaching serial ports
to the system, and under Linux it can be accessed at /dev/ttyUSBX.

# Building

The firmware uses the Open Source fx2lib, which will be downloaded as part of
the build process.

The build process requires git, make and sdcc. SDCC, the Small Device C
Compiler, is packaged in Debian and derivatives such as Ubuntu, as well as
Fedora:

`sudo apt-get install sdcc`
`sudo yum install sdcc`

`make`

# Flasing

Use fx2loader from the libfpgalink project:

`fx2loader -v 0925:3881 firmware.hex ram`


## Existing HDMI2USB USB endpoint usage

FIXME: Check this is correct!!!

| Endpoint | Direction | Transfer type | Used? | Comments                              |
| -------- | --------- | ------------- | ----- | --------------------------------------|
|     0    |     -     | CONTROL       | No    | USB Reserved                          |
|     1    |    IN     | INT           | Yes   | CDC Polling/Int?                      |
|     2    |    OUT    | BULK          | Yes   | Used for UART TX                      |
|     4    |    IN     | BULK          | Yes   | Used for UART RX                      |
|     6    |    IN     | BULK          | Yes   | Used for sending UVC camera data      |
|     8    |     -     | -             | No    | Unused, can be freed                  |


## What Cypress FX2LP supports

| Endpoint | Direction  | Transfer type | Comments                              |
| -------- | ---------- | ------------- | --------------------------------------|
|     0    |      -     | Control       | Reserved |
|     1    | IN and OUT | INT/BULK      | 64-byte buffers for smaller payloads |
|     2    | IN or OUT  | BULK/ISO/INT  | 512 or 1024 byte buffers for larger payloads |
|     4    | IN or OUT  | BULK/ISO/INT  |  |
|     6    | IN or OUT  | BULK/ISOINT   |  |
|     8    | IN or OUT  | BULK/ISO/INT  |  |



# References
    Create a USB Virtual COM Port: http://janaxelson.com/usb_virtual_com_port.htm
    USBCDC1.2 Spec PSTN120.pdf Page

