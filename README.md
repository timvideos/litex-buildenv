# LiteX Build Environment

[The LiteX Build Environment](https://github.com/timvideos/litex-buildenv)
is a tool for easily developing
[LiteX](https://github.com/enjoy-digital/litex) based systems. It was
originally designed to make the [TimVideos' HDMI2USB](https://hdmi2usb.tv) easy
to develop, but has now expanded to support multiple projects.

## Quick Links

 * [LiteX Build Environment Wiki](https://github.com/timvideos/litex-buildenv/wiki)
 * [Getting Started Guide](https://github.com/timvideos/litex-buildenv/wiki/Getting-Started)

 * TBD: [LiteX Build Environment Docs](https://litex-buildenv.readthedocs.io)

 * Dependency documentation
   - Migen - [[Website](http://m-labs.hk/migen/index.html)] [[User Guide](http://m-labs.hk/migen/manual/)] [[Code Repository](https://github.com/m-labs/migen)]
   - [Enjoy Digital Website](http://www.enjoy-digital.fr/)
   - [LiteX GitHub Repository](https://github.com/enjoy-digital/litex)

 * Projects using LiteX Build Environment:
   - [HDMI2USB](http://hdmi2usb.tv/) - The HDMI2USB project develops affordable hardware options to record and stream HD videos (from HDMI & DisplayPort sources) for conferences, meetings and user groups.
   - [FuPy](https://fupy.github.io) - The aim of the FuPy project is to make MicroPython run on FPGAs using the LiteX & Migen+MiSoC technologies. This allows you to do full stack development (FPGA gateware & soft CPU firmware) in Python!

---

## Important Terminology

 * [Gateware](https://github.com/litex-buildenv/wiki/Gateware) - The FPGA configuration.
 * [Soft CPU](https://github.com/litex-buildenv/wiki/Soft-CPU) - A CPU running inside the FPGA.
 * [Firmware](https://github.com/litex-buildenv/wiki/Firmware) - The software running on the `soft CPU` inside the FPGA.

## Structure

![LiteX BuildEnv Structure Image](https://docs.google.com/drawings/d/e/2PACX-1vTfB_DQ3PXJWKrERnzkGoWdKsTfuI3Kk-9rF1oBDB8NM44qZefU_O_H7rdNoN5cIWZmqzfIm1ftz52B/pub?w=419&h=485)

## [Boards](https://github.com/litex-buildenv/wiki/Boards)

The LiteX Build Environment supports a
[large number of FPGA boards](https://github.com/litex-buildenv/wiki/Boards),
but not all boards can be used for all projects.

## [Firmware](https://github.com/litex-buildenv/wiki/Firmware)

 * [HDMI2USB](https://github.com/litex-buildenv/wiki/HDMI2USB) - The firmware currently used for the HDMI2USB project.
 * [Bare Metal](https://github.com/litex-buildenv/wiki/Bare-Metal) - Your own firmware running directly on the soft CPU in the FPGA.
 * [Zephyr](https://github.com/litex-buildenv/wiki/Zephyr) - Support for [Zephyr RTOS](https://www.zephyrproject.org/).
 * [Linux](https://github.com/litex-buildenv/wiki/Linux) - Support for Linux.

## [Gateware](https://github.com/litex-buildenv/wiki/Gateware)

FIXME: Put stuff here.

## [Environment](https://github.com/litex-buildenv/wiki/Environment)

FIXME: Put stuff here.

## [Applications](https://github.com/litex-buildenv/wiki/Applications)

FIXME: Put stuff here.

![LiteX Application Relationship](https://docs.google.com/drawings/d/e/2PACX-1vTLVQXwkH3p5ZvN-7nIMxRXOyFEsg2x5_yrd3wREw3vaWr3Mc-_P7kfTbeQ--BN0k5VjQgxHchliyno/pub?w=1398&h=838)

## [Other Topics](https://github.com/litex-buildenv/wiki/Other-Topics)

FIXME: Put stuff here.

---

# License

This code was developed by the people found in the [AUTHORS](AUTHORS) file
(including major contributions from [EnjoyDigital](http://enjoy-digital.fr))
and released under a [BSD/MIT license](LICENSE).

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
