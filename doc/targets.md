
# Development Targets

### base

Basic SoC which has Soft CPU, DDR and UART working.

### net

Extends base with support for Ethernet.

### video

Adds video inputs + video outputs.

Useful if you are just working on video related stuff.

### memtest

SoC with extended memory testing infrastructure. 

Useful for verifying and testing performance of the DDR memory.

### bridge_`XXX`

SoC which doesn't have a Soft CPU master, only an wishbone bridge. 

XXX can be `uart`, `etherbone` or `pcie`.

Useful for quickly developing new cores as the minimal number of components
allows quick compilation of gateware.

### encoder

Net SoC with only the encoder. 

Useful for verifying and improving JPEG encoder.

---

# Real Targets

### hdmi2usb

Full HDMI2USB SoC including HDMI matrix, video capture, etc.

### TBA - scaler

SoC which does HDMI video mode conversion.

