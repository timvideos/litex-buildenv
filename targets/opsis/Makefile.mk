# opsis loading

TARGET ?= video

gateware-load-opsis: tftp
	opsis-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

firmware-load-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=$$(opsis-mode-switch --get-serial-dev) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-opsis:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

flash-opsis:
	opsis-mode-switch --verbose --flash-gateware=$(TARGET_BUILD_DIR)/gateware/top.bin
	opsis-mode-switch --verbose --flash-lm32-firmware=$(TARGET_BUILD_DIR)/software/firmware/firmware.fbi

.PHONY: gateware-load-opsis firmware-load-opsis reset-opsis flash-opsis
