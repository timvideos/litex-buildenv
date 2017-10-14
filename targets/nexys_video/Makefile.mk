# nexys_video loading

# Settings
DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-nexys_video: image-flash-py
	@true

.PHONY: image-flash-nexys_video

# Gateware
gateware-load-nexys_video:
	@echo "Not working yet."
	@false

gateware-flash-nexys_video: gateware-flash-py
	@true

.PHONY: gateware-load-nexys_video gateware-flash-nexys_video
# Firmware
firmware-load-nexys_video:
	@echo "Not working yet."
	@false

firmware-flash-nexys_video: firmwage-flash-py
	@true

firmware-connect-nexys_video:
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

.PHONY: firmware-load-nexys_video firmware-flash-nexys_video firmware-connect-nexys_video

# Bios
bios-flash-nexys_video:
	@echo "Not working yet"
	@false

.PHONY: bios-flash-nexys_video

# Extra commands
help-nexys_video:
	@true

.PHONY: help-nexys_video
