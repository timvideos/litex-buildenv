# netv2 targets

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
	@echo "Unsupported."
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)
# Firmware
firmware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-connect-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-clear-$(PLATFORM):
	@echo "FIXME: Unsupported?."
	@false

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-connect-$(PLATFORM) firmware-clear-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: bios-flash-$(PLATFORM)

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: help-$(PLATFORM) reset-$(PLATFORM)
