# atlys loading
load-gateware-atlys: tftp
	atlys-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

load-firmware-atlys:
	atlys-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/atlys0/tty --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-atlys:
	atlys-mode-switch --verbose --mode=serial
	atlys-mode-switch --verbose --mode=jtag
	atlys-mode-switch --verbose --mode=serial

.PHONY: load-gateware-atlys load-firmware-atlys reset-atlys
