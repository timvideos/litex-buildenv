# opsis loading

DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

gateware-load-opsis:
	opsis-mode-switch --verbose --load-gateware $(GATEWARE_FILEBASE).bit
	opsis-mode-switch --verbose --reset-gateware

gateware-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(GATEWARE_FILEBASE).bin
	opsis-mode-switch --verbose --reset-gateware

firmware-load-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev) --kernel=$(FIRMWARE_FILEBASE).bin

firmware-flash-opsis:
	opsis-mode-switch --verbose --flash-softcpu-firmware=$(FIRMWARE_FILEBASE).fbi
	opsis-mode-switch --verbose --reset-gateware

firmware-connect-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev)

image-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(IMAGE_FILE)
	opsis-mode-switch --verbose --reset-gateware

bios-flash-opsis:
	opsis-mode-switch --verbose --flash-softcpu-bios=$(BIOS_FILE)
	opsis-mode-switch --verbose --reset-gateware

reset-opsis:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

help-opsis:
	@echo " make reset-opsis"

.PHONY: gateware-load-opsis firmware-load-opsis reset-opsis flash-opsis
