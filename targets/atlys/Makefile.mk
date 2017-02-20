# atlys loading

TARGET ?= video

gateware-load-atlys: tftp
	atlys-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

firmware-load-atlys:
	flterm --port=$$(atlys-mode-switch --get-serial-device) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-atlys:
	atlys-mode-switch --verbose --mode=jtag

flash-atlys:
	atlys-mode-switch --verbose --flash-gateware=$(TARGET_BUILD_DIR)/gateware/top.bin
	atlys-mode-switch --verbose --flash-lm32-firmware=$(TARGET_BUILD_DIR)/software/firmware/firmware.fbi

.PHONY: gateware-load-atlys firmware-load-atlys reset-atlys flash-opsis
