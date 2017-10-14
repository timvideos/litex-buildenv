# pipistrello targets

ifneq ($(PLATFORM),pipistrello)
	$(error "Platform should be pipistrello when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

PROG_PORT ?= /dev/ttyUSB0
COMM_PORT ?= /dev/ttyUSB1
BAUD ?= 115200

# Image
image-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: image-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)

# Firmware
firmware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-connect-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-connect-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: bios-flash-$(PLATFORM)

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported."
	@false


.PHONY: help-$(PLATFORM) reset-$(PLATFORM)
