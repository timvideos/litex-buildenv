# minispartan6 loading
load-gateware-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(TARGET_BUILD_DIR)/gateware/top.bit; exit"

load-firmware-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

.PHONY: load-gateware-minispartan6 load-firmware-minispartan6
