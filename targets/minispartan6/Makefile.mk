# minispartan6 loading

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

PROG_PORT ?= /dev/ttyUSB0
COMM_PORT ?= /dev/ttyUSB1
BAUD ?= 115200

# Image
image-flash-minispartan6:
	@echo "Unsupported"
	@false

.PHONY: image-flash-minispartan6

# Gateware
gateware-load-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(GATEWARE_FILEBASE).bit; exit"

gateware-flash-minispartan6:
	@echo "Unsupported"
	@false

.PHONY: gateware-load-minispartan6 gateware-flash-minispartan6

# Firmware
firmware-load-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-minispartan6:
	@echo "Unsupported."
	@false

firmware-connect-minispartan6:
	@echo "Unsupported."
	@false

.PHONY: firmware-load-minispartan6 firmware-flash-sim firmware-connect-minispartan6

# Bios
bios-flash-minispartan6:
	@echo "Unsupported."
	@false

.PHONY: bios-flash-minispartan6

# Extra commands
help-minispartan6:
	@true

.PHONY: help-minispartan6
