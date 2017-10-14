# arty loading

# Settings
DEFAULT_TARGET = net
TARGET ?= $(DEFAULT_TARGET)

PROG_PORT ?= /dev/ttyUSB0
COMM_PORT ?= /dev/ttyUSB1
BAUD ?= 115200

# Image
image-flash-arty: image-flash-py
	@true

.PHONY: image-flash-arty

# Gateware
gateware-load-arty:
	openocd -f board/digilent_arty.cfg -c "init; pld load 0 $(TARGET_BUILD_DIR)/gateware/top.bit; exit"

gateware-flash-arty: gateware-flash-py
	@true

.PHONY: gateware-load-arty gateware-flash-arty

# Firmware
firmware-load-arty:
	flterm --port=$(COMM_PORT) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin --speed=$(BAUD)

firmware-flash-arty: firmwage-flash-py
	@true

firmware-connect-arty:
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

.PHONY: firmware-load-arty firmware-flash-arty firmware-connect-arty

# Bios
bios-flash-arty:
	@echo "Not working yet"
	@false

.PHONY: bios-flash-arty

# Extra commands
help-arty:
	@true

.PHONY: help-arty
