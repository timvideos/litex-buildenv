# tinyfpga_bx targets

ifneq ($(PLATFORM),tinyfpga_bx)
	$(error "Platform should be tinyfpga_bx when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)
BAUD ?= 115200
PROG_PORT ?=
COMM_PORT ?= /dev/ttyACM0

ifneq ($(PROG_PORT),)
PROG_EXTRA_ARGS=-c $(PROG_PORT)
else
PROG_EXTRA_ARGS=
endif

# Image
image-flash-$(PLATFORM):
	tinyprog $(PROG_EXTRA_ARGS) --program-image $(IMAGE_FILE)

# Gateware
gateware-load-$(PLATFORM):
	@echo "TinyFPGA BX doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

# As with Mimasv2, if the user asks to flash the gateware only, the BIOS must
# be sent as well (because the BIOS is too big to fit into the bitstream).
GATEWARE_BIOS_FILE = $(TARGET_BUILD_DIR)/image-gateware+bios+none.bin

gateware-flash-$(PLATFORM): $(GATEWARE_BIOS_FILE)
	tinyprog $(PROG_EXTRA_ARGS) --program-image $(GATEWARE_BIOS_FILE)

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
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM):
	@echo "TinyFPGA BX doesn't support just flashing firmware, use image target instead."
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
