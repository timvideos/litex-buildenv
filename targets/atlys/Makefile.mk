# atlys loading

DEFAULT_TARGET = video
TARGET ?= $(DEFAULT_TARGET)

gateware-load-atlys: tftp
	atlys-mode-switch --verbose --load-gateware $(GATEWARE_FILEBASE).bit

firmware-load-atlys:
	flterm --port=$$(atlys-mode-switch --get-serial-device) --kernel=$(FIRMWARE_FILEBASE).bin

reset-atlys:
	atlys-mode-switch --verbose --mode=jtag

flash-atlys:
	atlys-mode-switch --verbose --flash-gateware=$(GATEWARE_FILEBASE).bin
	atlys-mode-switch --verbose --flash-softcpu-firmware=$(FIRMWARE_FILEBASE).fbi

help-atlys:
	@echo " make reset-atlys"

.PHONY: gateware-load-atlys firmware-load-atlys reset-atlys flash-atlys help-atlys
