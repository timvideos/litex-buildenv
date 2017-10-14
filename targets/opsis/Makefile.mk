# opsis loading

# Settings
DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(IMAGE_FILE)
	opsis-mode-switch --verbose --reset-gateware

.PHONY: image-flash-opsis

# Gateware
gateware-load-opsis:
	opsis-mode-switch --verbose --load-gateware $(GATEWARE_FILEBASE).bit
	opsis-mode-switch --verbose --reset-gateware

gateware-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(GATEWARE_FILEBASE).bin
	opsis-mode-switch --verbose --reset-gateware

.PHONY: gateware-load-opsis gateware-flash-opsis

# Firmware
firmware-load-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev) --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-opsis:
	opsis-mode-switch --verbose --flash-softcpu-firmware=$(FIRMWARE_FILEBASE).fbi
	opsis-mode-switch --verbose --reset-gateware

firmware-connect-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev)

.PHONY: firmware-load-opsis firmware-flash-opsis firmware-connect-opsis

# Bios
bios-flash-opsis:
	opsis-mode-switch --verbose --flash-softcpu-bios=$(BIOS_FILE)
	opsis-mode-switch --verbose --reset-gateware

.PHONY: bios-flash-opsis

# Extra commands
help-opsis:
	@echo " make reset-opsis"

reset-opsis:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

.PHONY: help-opsis
.PHONY: reset-opsis
