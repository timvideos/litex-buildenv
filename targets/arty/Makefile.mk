# arty loading

TARGET ?= net

PROG_PORT ?= /dev/ttyUSB0
COMM_PORT ?= /dev/ttyUSB1
BAUD ?= 115200

gateware-load-arty:
	openocd -f board/digilent_arty.cfg -c "init; pld load 0 $(TARGET_BUILD_DIR)/gateware/top.bit; exit"

gateware-flash-arty: gateware-flash-py
	@true

image-load-arty:
	echo "Not working yet."
	false

image-flash-arty: image-flash-py
	@true

firmware-load-arty:
	flterm --port=$(COMM_PORT) --kernel=$(TARGET_BUILD_DIR)/software/firmware/firmware.bin --speed=$(BAUD)

firmware-flash-arty: firmwage-flash-py
	@true

firmware-connect-arty:
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

.PHONY: gateware-load-arty gateware-flash-arty
.PHONY: image-load-arty image-flash-arty
.PHONY: firmware-load-arty firmware-flash-arty firmware-connect-arty
