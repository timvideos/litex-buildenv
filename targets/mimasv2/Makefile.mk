# mimasv2 loading
load-gateware-mimasv2:
	MimasV2Config.py /dev/ttyACM0 $(TARGET_BUILD_DIR)/gateware/top.bin

load-firmware-mimasv2:
	flterm --port=/dev/ttyACM0 --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

.PHONY: load-gateware-mimasv2 load-firmware-mimasv2
