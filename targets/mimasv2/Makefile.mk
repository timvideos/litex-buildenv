# mimasv2 targets

ifneq ($(PLATFORM),mimasv2)
	$(error "Platform should be mimasv2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

# FIXME(mithro): Detect the real serial port/add see udev rules to HDMI2USB-mode-switch...
ifeq ($(JIMMO),)
PORT ?= /dev/ttyACM0
PROG_PORT ?= $(PORT)
COMM_PORT ?= $(PORT)
BAUD ?= 19200
else
PROG_PORT ?= /dev/ttyACM0
COMM_PORT ?= /dev/ttyACM1
BAUD ?= 115200
endif

# Image
image-flash-$(PLATFORM):
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(IMAGE_FILE)

# Gateware
gateware-load-$(PLATFORM):
	@echo "MimasV2 doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

gateware-flash-$(PLATFORM):
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(GATEWARE_FILEBASE).bin

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)

firmware-flash-$(PLATFORM):
	@echo "MimasV2 doesn't support just flashing firmware, use image target instead."
	@echo "make image-flash"
	@false

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

firmware-clear-$(PLATFORM):
	@echo "FIXME: Unsupported?."
	@false

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
