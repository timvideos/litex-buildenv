# nexys_video targets

ifneq ($(PLATFORM),nexys_video)
	$(error "Platform should be nexys_video when using this file!?")
endif

# Settings
DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-$(PLATFORM): image-flash-py
	@true

.PHONY: image-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

gateware-flash-$(PLATFORM): gateware-flash-py
	@true

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)
# Firmware
firmware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM): firmwage-flash-py
	@true

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

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
