# Pano Logic Zero Client G2 targets

ifneq ($(PLATFORM),pano_logic_g2)
	$(error "Platform should be pano_logic_g2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

COMM_PORT ?= /dev/ttyUSB0
BAUD ?= 115200

# Image
image-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported"
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)

firmware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported"
	@false
