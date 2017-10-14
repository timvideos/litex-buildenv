# minispartan6 loading

ifneq ($(PLATFORM),minispartan6)
	$(error "Platform should be minispartan6 when using this file!?")
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
	openocd -f board/$(PLATFORM).cfg -c "init; pld load 0 $(GATEWARE_FILEBASE).bit; exit"

gateware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=/dev/ttyUSB1 --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-connect-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: firmware-load-$(PLATFORM) firmware-flash-sim firmware-connect-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: bios-flash-$(PLATFORM)

# Extra commands
help-$(PLATFORM):
	@true

.PHONY: help-$(PLATFORM)
