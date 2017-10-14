# pipistrello loading

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

PROG_PORT ?= /dev/ttyUSB0
COMM_PORT ?= /dev/ttyUSB1
BAUD ?= 115200

# Image
image-flash-pipistrello:
	@echo "Unsupported"
	@false

.PHONY: image-flash-pipistrello

# Gateware
gateware-load-pipistrello:
	@echo "Not working yet."
	@false

gateware-flash-pipistrello:
	@echo "Unsupported"
	@false

.PHONY: gateware-load-pipistrello gateware-flash-pipistrello

# Firmware
firmware-load-pipistrello:
	@echo "Not working yet."
	@false

firmware-flash-pipistrello:
	@echo "Unsupported."
	@false

firmware-connect-pipistrello:
	@echo "Unsupported."
	@false

.PHONY: firmware-load-pipistrello firmware-flash-sim firmware-connect-pipistrello

# Bios
bios-flash-pipistrello:
	@echo "Unsupported."
	@false

.PHONY: bios-flash-pipistrello

# Extra commands
help-pipistrello:
	@true

.PHONY: help-pipistrello
