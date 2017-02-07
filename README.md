# HDMI2USB MiSoC Firmware

## Quick Links

 * [HDMI2USB user documentation](http://hdmi2usb.tv/)
 * [HDMI2USB Firmware documentation](https://hdmi2usb.tv/firmware-misoc)
 * [Report a bug](https://github.com/timvideos/HDMI2USB-misoc-firmware/issues/new)
 * [misoc + migen website](http://m-labs.hk/gateware.html)

# Table of contents

  * Overview
  * HDMI2USB MiSoC Firmware
    * Supported Boards
    * Development Boards
  * Getting started
  * Documentation
  * Current Status
    * HDMI2USB
      * Atlys
      * Opsis
    * HDMI2Eth
      * Atlys
    * Base
      * Atlys
      * Opsis
      * Pipistrello
      * miniSpartan6+
  * License
  * Contact

# Overview

**The HDMI2USB project develops affordable hardware options to record and
stream HD videos (from HDMI & DisplayPort sources) for conferences, meetings
and user groups.**

We are currently developing our own hardware (the
[Numato Opsis](https://hdmi2usb.tv/numato-opsis), and also provide firmware for
various prototyping boards.

HDMI2USB started in 2013, and is an active ongoing project in its third
iteration of hardware prototyping.  Today you can download early working
firmware and have real capture happen, but we actively wish to improve and are
seeking assistance:

  * **For video recording individuals+teams:** Be an early adopter; get a
    board, start using it, report back to us with feedback

  * **For software/FPGA developers:** Get involved in contributing code both to
    the capture software + FPGA stack

Our aim is this becomes the defacto, incredibly affordable and easy to use
video recording hardware for conferences, meetings and user groups worldwide.

**Find out more about HDMI2USB and why we're doing this in [ABOUT + FAQ](http://hdmi2usb.tv/faq)**

![HDMI2USB Diagram](https://hdmi2usb.tv/img/hdmi2usb.png "HDMI2USB Diagram")

# HDMI2USB MiSoC Firmware

## Supported Boards

This firmware is supported on the following to boards;

 * [Digilent Atlys](https://hdmi2usb.tv/digilent-atlys/) - `BOARD=atlys` - http://digilentinc.com/atlys/

   The original board used for HDMI2USB prototyping.

   ![Digilent Atlys Picture](https://hdmi2usb.tv/img/digilent-atlys-small.jpg)

 * [Numato Opsis](https://hdmi2usb.tv/numato-opsis/) - `BOARD=opsis` - https://crowdsupply.com/numato-lab/opsis

   The first production board made in conjunction with TimVideos.us project.

   ![Numato Opsis Picture](https://hdmi2usb.tv/img/numato-opsis-small.jpg)

For a comparison between the supported boards, see the 
[HDMI2USB Hardware page](https://hdmi2usb.tv/hardware/).

## Development Boards

 * Pipistrello - http://pipistrello.saanlima.com/

   `BOARD=pipistrello`

   A small FPGA board with only one HDMI output port.
   Due to the lack of video *inputs*, this board is only useful for developers.

 * miniSpartan6+ - https://www.scarabhardware.com/minispartan6/ -
   [*In progress*](https://github.com/timvideos/HDMI2USB-misoc-firmware/tree/minispartan6%2B)

   `BOARD=miniSpartan`

   A small FPGA board with HDMI input and HDMI output.
   Due to the low speed ram and USB interface, this board is only useful for
   developers who want to work on the HDMI subsystem and need a small board
   that fits in their pocket.

# Getting started

For **using** a HDMI2USB board, prebuilt versions of the firmware are available in
the 
[HDMI2USB-firmware-prebuilt](http://github.com/timvideos/HDMI2USB-firmware-prebuilt)
repository.

For **helping with the development**, instructions for setting up the build
environment are found in the [scripts/README.md](scripts/) file.

# Documentation

**User** documentation is found on the [HDMI2USB website](https://hdmi2usb.tv).

High level **developer** documentation for the firmware can be found in the
[doc](doc/) directory. More documentation is found in the source code.

![System Diagram](doc/architecture.png)

# Current Status

## HDMI2USB

The `hdmi2usb` targets are for doing capturing and streaming using the FX2 USB
interface.

### Atlys

[`atlys_hdmi2usb`](targets/atlys_hdmi2usb.py)

* `VideomixerSoC` validated: MiniSoC + 2 x HDMI in + 2 x HDMI out
* `HDMI2USBSoC` validated: VideomixerSoC + JPEG encoder + USB streaming

### Opsis

[`opsis_hdmi2usb`](targets/opsis_hdmi2usb.py)

* `VideomixerSoC` validated: MiniSoC + 2 x HDMI in + 2 x HDMI out
* `HDMI2USBSoC` validated: VideomixerSoC + JPEG encoder + USB streaming

## HDMI2Eth

The `hdmi2eth` targets are for doing capturing and control using the Ethernet
found on many boards.

### Atlys

[`atlys_hdmi2eth`](targets/atlys_hdmi2eth.py)

* `EtherboneSoC` validated: BaseSoC + 10/100Mbps HW Ethernet UDP/IP stack and
  Etherbone

* `VideomixerSoC` validated: EtherboneSoC + HDMI in + HDMI out
* `HDMI2ETHSoC` validated: VideomixerSoC + JPEG encoder + UDP streaming

## Base

The `base` targets are used during initial bring up and verification of basic
features. Getting MiniSoc running on new hardware is the first step towards
supporting it. All the other, more functional, targets are built on top of this
target.

### Atlys

[`atlys_base`](targets/atlys_base.py)

* `BaseSoC` validated: CPU + DDR2 + UART
* `MiniSoC` validated: BaseSoC + 10/100Mbps Ethernet MAC handled by the CPU

### Opsis

[`opsis_base`](targets/opsis_base.py)

* `BaseSoC` validated: CPU + DDR3 + UART
* `MiniSoC` validated: BaseSoC + 1Gbps Ethernet MAC handled by the CPU

### Pipistrello

[`pipistrello_base`](targets/pipistrello_base.py)

* `BaseSoC`: CPU + LPDDR + UART
* `VideomixerSoC`: BaseSoC + HDMI out

### miniSpartan6+

* `BaseSoC`: CPU + UART

# License

This code was original developed by [EnjoyDigital](http://enjoy-digital.fr)
and unless otherwise noted is;
 * Copyright (C) 2015 / TimVideo.us
 * Copyright (C) 2015 / EnjoyDigital

and released under a [BSD/MIT license](LICENSE). This includes the
[gateware](gateware/), the [lm32 firmware](firmware/lm32/) and related files.

The [FX2 firmware](firmware/fx2) is under the
[GPL version 2.0 (or later)](http://www.gnu.org/licenses/gpl-2.0.en.html).

Code under the [third_party](third_party/) directory comes from external
sources and is available in their own licenses.

# Contact

TimVideo.us:

 * Mailing List:
   * https://groups.google.com/forum/#!forum/hdmi2usb
     [[Join](https://groups.google.com/forum/#!forum/hdmi2usb/join)]
   * hdmi2usb@googlegroups.com

 * IRC:
   * irc://irc.freenode.net/#timvideos
     [[Web Interface](http://webchat.freenode.net/?channels=timvideos)]

EnjoyDigital:
 * florent@enjoy-digital.fr
