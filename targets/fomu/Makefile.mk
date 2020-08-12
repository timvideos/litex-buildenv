# fomu targets

ifneq ($(PLATFORM),fomu)
	$(error "Platform should be ice40-up5k-uwg30 or ice40-up5k-sg48 when using this file!?")
endif

PPATH := $(PYTHONPATH)
export PYTHONPATH=$(PPATH):$(TARGET_BUILD_DIR)/../../third_party/valentyusb/

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)
BAUD ?= 115200

# Image
image-flash-$(PLATFORM):
	cp $(IMAGE_FILE) $(IMAGE_FILE).dfu
	dfu-suffix --pid 1209 --vid 5bf0 --add $(IMAGE_FILE).dfu
	dfu-util -D $(IMAGE_FILE).dfu

# Gateware
gateware-load-$(PLATFORM):
	@echo "Fomu doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

# As with Mimasv2, if the user asks to flash the gateware only, the BIOS must
# be sent as well (because the BIOS is too big to fit into the bitstream).
#
# We have to pre-calculate what the image file will end up being, as we are
# included before it has been defined (to get the default target), so we'll
# end up comparing with an empty string/older value from the environment.
#
GATEWARE_BIOS_FILE = $(TARGET_BUILD_DIR)/image-gateware+bios+none.bin
IMAGE_FW_FILE      = $(TARGET_BUILD_DIR)/image-gateware+bios+$(FIRMWARE).bin

gateware-flash-$(PLATFORM): $(GATEWARE_BIOS_FILE)
	cp $(GATEWARE_BIOS_FILE) $(GATEWARE_BIOS_FILE).dfu
	dfu-suffix --pid 1209 --vid 5bf0 --add $(GATEWARE_BIOS_FILE).dfu
	dfu-util -D $(GATEWARE_BIOS_FILE).dfu

# To avoid duplicating the mkimage.py call here, if the user has not
# already built a image-gateware+bios+none.bin, we call make recursively
# to build one here, with the FIRMWARE=none override.
#
ifneq ($(GATEWARE_BIOS_FILE),$(IMAGE_FW_FILE))
$(GATEWARE_BIOS_FILE): $(GATEWARE_FILEBASE).bin $(BIOS_FILE) mkimage.py
	FIRMWARE=none make image
endif

# Firmware
firmware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM):
	@echo "Fomu doesn't support just flashing firmware, use gateware target instead."
	@echo "make image-flash"
	@false

firmware-connect-$(PLATFORM):
	@echo "FIXME: Unsupported?."
	@false

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
