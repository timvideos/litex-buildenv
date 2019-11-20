# netv2 targets

ifneq ($(PLATFORM),netv2)
	$(error "Platform should be netv2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = net
TARGET ?= $(DEFAULT_TARGET)

COMM_PORT ?= /dev/ttyUSB0
BAUD ?= 115200

# Image
image-flash-$(PLATFORM): image-flash-py
	@true

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported"
	@false

gateware-flash-$(PLATFORM): gateware-flash-py
	@true

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)


firmware-flash-$(PLATFORM): firmware-flash-py
	@true

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported."
	@false
