# netv2 loading

# Settings
DEFAULT_TARGET = pcie
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-netv2:
	@echo "Unsupported"
	@false

.PHONY: image-flash-netv2

# Gateware
gateware-load-netv2:
	@echo "Not working yet."
	@false

gateware-flash-netv2:
	@echo "Unsupported"
	@false

.PHONY: gateware-load-netv2 gateware-flash-netv2
# Firmware
load-firmware-netv2:
	@echo "Not working yet."
	@false

firmware-flash-netv2:
	@echo "Unsupported."
	@false

firmware-connect-netv2:
	@echo "Unsupported."
	@false

.PHONY: firmware-load-netv2 firmware-flash-sim firmware-connect-netv2

# Bios
bios-flash-netv2:
	@echo "Unsupported."
	@false

.PHONY: bios-flash-netv2

# Extra commands
help-netv2:
	@true

.PHONY: help-netv2
