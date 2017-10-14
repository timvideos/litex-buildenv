# nexys_video loading

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
	@echo "Not working yet."
	@false

gateware-flash-$(PLATFORM): gateware-flash-py
	@true

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)
# Firmware
firmware-load-$(PLATFORM):
	@echo "Not working yet."
	@false

firmware-flash-$(PLATFORM): firmwage-flash-py
	@true

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-connect-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	@echo "Not working yet"
	@false

.PHONY: bios-flash-$(PLATFORM)

# Extra commands
help-$(PLATFORM):
	@true

.PHONY: help-$(PLATFORM)
