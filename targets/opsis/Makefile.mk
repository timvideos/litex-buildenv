# opsis loading

TARGET ?= video

gateware-load-opsis:
	opsis-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit
	opsis-mode-switch --verbose --reset-gateware

gateware-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(TARGET_BUILD_DIR)/gateware/top.bin
	opsis-mode-switch --verbose --reset-gateware

firmware-load-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

firmware-flash-opsis:
	opsis-mode-switch --verbose --flash-lm32-firmware=$(TARGET_BUILD_DIR)/software/firmware/firmware.fbi
	opsis-mode-switch --verbose --reset-gateware

firmware-connect-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev)

image-flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(TARGET_BUILD_DIR)/flash.bin
	opsis-mode-switch --verbose --reset-gateware

reset-opsis:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

.PHONY: gateware-load-opsis firmware-load-opsis reset-opsis flash-opsis
