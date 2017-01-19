# atlys loading

TARGET ?= video

gateware-load-atlys: tftp
	atlys-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

firmware-load-atlys:
	atlys-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/atlys0/tty --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-atlys:
	atlys-mode-switch --verbose --mode=serial
	atlys-mode-switch --verbose --mode=jtag
	atlys-mode-switch --verbose --mode=serial

.PHONY: gateware-load-atlys firmware-load-atlys reset-atlys
