# minispartan6 loading

TARGET ?= base

gateware-load-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(TARGET_BUILD_DIR)/gateware/top.bit; exit"

firmware-load-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin

.PHONY: gateware-load-minispartan6 firmware-load-minispartan6
