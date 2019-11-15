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
	$(PYTHON) -m MimasV2.Config $(PROG_PORT) $(IMAGE_FILE)

# Gateware
gateware-load-$(PLATFORM):
	@echo "MimasV2 doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

# On Mimas v2 both the gateware and the BIOS need to be in the same flash,
# which means that they can only really usefully be updated together.  As
# a result we should flash "Gateware + BIOS + no application" if the user
# asks us to flash the gatware.  This mirrors the behaviour of embedding
# the BIOS in the Gateware loaded via gateware-load, on other platforms,
# eg, on the Arty.
#
GATEWARE_BIOS_FILE = $(TARGET_BUILD_DIR)/image-gateware+bios+none.bin

gateware-flash-$(PLATFORM): $(GATEWARE_BIOS_FILE)
	$(PYTHON) -m MimasV2.Config $(PROG_PORT) $(GATEWARE_BIOS_FILE)

# To avoid duplicating the mkimage.py call here, if the user has not
# already built a image-gateware+bios+none.bin, we call make recursively
# to build one here, with the FIRMWARE=none override.
#
ifneq ($(GATEWARE_BIOS_FILE),$(IMAGE_FILE))
$(GATEWARE_BIOS_FILE): $(GATEWARE_FILEBASE).bin $(BIOS_FILE) mkimage.py
	FIRMWARE=none make image
endif

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
