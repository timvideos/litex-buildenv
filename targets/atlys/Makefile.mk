# atlys loading

# Settings
DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-atlys:
	atlys-mode-switch --verbose --flash-gateware=$(IMAGE_FILE)
	atlys-mode-switch --verbose --reset-gateware

.PHONY: image-flash-atlys

# Gateware
gateware-load-atlys:
	atlys-mode-switch --verbose --load-gateware $(GATEWARE_FILEBASE).bit

gateware-flash-atlys:
	atlys-mode-switch --verbose --flash-gateware=$(GATEWARE_FILEBASE).bin
	atlys-mode-switch --verbose --reset-gateware

.PHONY: gateware-load-atlys gateware-flash-atlys

# Firmware
firmware-load-atlys:
	flterm --port=$$(atlys-mode-switch --get-serial-device) --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-atlys:
	atlys-mode-switch --verbose --flash-softcpu-firmware=$(FIRMWARE_FILEBASE).fbi
	atlys-mode-switch --verbose --reset-gateware

firmware-connect-atlys:
	flterm --port=$$(atlys-mode-switch --get-serial-dev)

.PHONY: firmware-load-atlys firmware-flash-atlys firmware-connect-atlys

# Bios
bios-flash-atlys:
	atlys-mode-switch --verbose --flash-softcpu-bios=$(BIOS_FILE)
	atlys-mode-switch --verbose --reset-gateware

.PHONY: bios-flash-atlys

# Extra commands
help-atlys:
	@echo " make reset-atlys"

reset-atlys:
	atlys-mode-switch --verbose --mode=jtag

.PHONY: help-atlys
.PHONY: reset-atlys
