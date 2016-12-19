# opsis loading
load-gateware-opsis: tftp
	opsis-mode-switch --verbose --load-gateware $(TARGET_BUILD_DIR)/gateware/top.bit

load-firmware-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/opsis0/tty --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

reset-opsis:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

.PHONY: load-gateware-opsis load-firmware-opsis reset-opsis
