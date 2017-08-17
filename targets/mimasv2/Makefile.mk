# mimasv2 loading

DEFAULT_TARGET = base

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

gateware-load-mimasv2:
	@echo "MimasV2 doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

gateware-flash-mimasv2:
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(GATEWARE_FILEBASE).bin

image-load-mimasv2:
	@echo "MimasV2 doesn't support loading, use the flash target instead."
	@echo "make image-flash"
	@false

image-flash-mimasv2:
	$(PYTHON) $$(which MimasV2Config.py) $(PROG_PORT) $(IMAGE_FILE)

firmware-load-mimasv2:
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)

firmware-flash-mimasv2:
	@echo "MimasV2 doesn't support just flashing firmware, use image target instead."
	@echo "make image-flash"
	@false

firmware-connect-mimasv2:
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

help-mimasv2:
	@true

.PHONY: gateware-load-mimasv2 firmware-load-mimasv2 help-mimasv2
