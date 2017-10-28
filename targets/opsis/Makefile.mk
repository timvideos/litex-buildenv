# opsis targets

ifneq ($(PLATFORM),opsis)
	$(error "Platform should be opsis when using this file!?")
endif

# Settings
DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --flash-gateware=$(IMAGE_FILE)
	$(PLATFORM)-mode-switch --verbose --reset-gateware

.PHONY: image-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --load-gateware $(GATEWARE_FILEBASE).bit
	$(PLATFORM)-mode-switch --verbose --reset-gateware

gateware-flash-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --flash-gateware=$(GATEWARE_FILEBASE).bin
	$(PLATFORM)-mode-switch --verbose --reset-gateware

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)

# Firmware
firmware-load-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --mode=serial
	flterm --port=$$($(PLATFORM)-mode-switch --get-serial-dev) --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --flash-softcpu-firmware=$(FIRMWARE_FILEBASE).fbi
	$(PLATFORM)-mode-switch --verbose --reset-gateware

firmware-connect-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --mode=serial
	flterm --port=$$($(PLATFORM)-mode-switch --get-serial-dev)

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-connect-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --flash-softcpu-bios=$(BIOS_FILE)
	$(PLATFORM)-mode-switch --verbose --reset-gateware

.PHONY: bios-flash-$(PLATFORM)

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	$(PLATFORM)-mode-switch --verbose --mode=serial
	$(PLATFORM)-mode-switch --verbose --mode=jtag
	$(PLATFORM)-mode-switch --verbose --mode=serial

.PHONY: help-$(PLATFORM) reset-$(PLATFORM)
