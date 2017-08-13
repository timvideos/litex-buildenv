# minispartan6 loading

DEFAULT_TARGET = base

gateware-load-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(GATEWARE_FILEBASE).bit; exit"

firmware-load-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(FIRMWARE_FILEBASE).bin

help-minispartan6:
	@true

.PHONY: gateware-load-minispartan6 firmware-load-minispartan6 help-minispartan6
