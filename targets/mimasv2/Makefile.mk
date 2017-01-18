# mimasv2 loading
gateware-load-mimasv2:
	python3 $$(which MimasV2Config.py) /dev/ttyACM0 $(TARGET_BUILD_DIR)/gateware/top.bin

image-load-mimasv2:
	python mkimage.py
	python3 $$(which MimasV2Config.py) /dev/ttyACM0 $(TARGET_BUILD_DIR)/flash.bin

firmware-load-mimasv2:
	flterm --port=/dev/ttyACM0 --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin --speed=19200

firmware-connect-mimasv2:
	flterm --port=/dev/ttyACM0 --speed=19200

.PHONY: gateware-load-mimasv2 firmware-load-mimasv2
