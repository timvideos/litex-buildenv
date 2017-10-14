# netv2 loading

ifneq ($(PLATFORM),netv2)
	$(error "Platform should be netv2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = pcie
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: image-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	@echo "Not working yet."
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)
# Firmware
load-firmware-$(PLATFORM):
	@echo "Not working yet."
	@false

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
