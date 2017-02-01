# mimasv2 loading

TARGET ?= base
# FIXME(mithro): Detect the real serial port/add see udev rules to HDMI2USB-mode-switch...
PORT ?= /dev/ttyACM0

gateware-load-mimasv2:
	python3 $$(which MimasV2Config.py) $(PORT) $(TARGET_BUILD_DIR)/gateware/top.bin

image-load-mimasv2:
	python mkimage.py
	python3 $$(which MimasV2Config.py) $(PORT) $(TARGET_BUILD_DIR)/flash.bin

firmware-load-mimasv2:
	flterm --port=$(PORT) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin --speed=19200

firmware-connect-mimasv2:
	flterm --port=$(PORT) --speed=19200

.PHONY: gateware-load-mimasv2 firmware-load-mimasv2
