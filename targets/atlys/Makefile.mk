# atlys loading

TARGET ?= video

gateware-load-atlys: tftp
	atlys-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

firmware-load-atlys:
	flterm --port=$$(atlys-mode-switch --get-serial-device) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-atlys:
	atlys-mode-switch --verbose --mode=jtag

.PHONY: gateware-load-atlys firmware-load-atlys reset-atlys
