# mimasv2 loading
gateware-load-mimasv2:
	MimasV2Config.py /dev/ttyACM0 $(TARGET_BUILD_DIR)/gateware/top.bin

firmware-load-mimasv2:
	flterm --port=/dev/ttyACM0 --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

.PHONY: gateware-load-mimasv2 firmware-load-mimasv2
