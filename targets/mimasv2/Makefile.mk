# mimasv2 loading

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
image-flash-mimasv2:
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(IMAGE_FILE)

.PHONY: image-flash-mimasv2

# Gateware
gateware-load-mimasv2:
	@echo "MimasV2 doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

gateware-flash-mimasv2:
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(GATEWARE_FILEBASE).bin

.PHONY: gateware-load-mimasv2 gateware-flash-mimasv2
# Firmware
firmware-load-mimasv2:
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)

firmware-flash-mimasv2:
	@echo "MimasV2 doesn't support just flashing firmware, use image target instead."
	@echo "make image-flash"
	@false

firmware-connect-mimasv2:
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

.PHONY: firmware-load-mimasv2 firmware-flash-mimasv2 firmware-connect-mimasv2

# Bios
bios-flash-mimasv2:
	@echo "Unsupported."
	@false

.PHONY: bios-flash-mimasv2

# Extra commands
help-mimasv2:
	@true

.PHONY: help-mimasv2
