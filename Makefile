BOARD ?= opsis
MSCDIR ?= ../misoc
PROG ?= impact
SERIAL ?= /dev/ttyVIZ0
TARGET ?= hdmi2usb

HDMI2USBDIR = ../HDMI2USB-misoc-firmware
PYTHON = python3

CMD = $(PYTHON) make.py -X $(HDMI2USBDIR) -t $(BOARD)_$(TARGET) -Ot firmware_filename $(HDMI2USBDIR)/firmware/lm32/firmware.bin -Op programmer $(PROG)

ifeq ($(OS),Windows_NT)
	FLTERM = $(PYTHON) $(MSCDIR)/tools/flterm.py
else
	FLTERM = $(MSCDIR)/tools/flterm
endif

help:
	@echo "Targets avaliable:"
	@echo " make gateware"
	@echo " make load-gateware"
	@echo " make load-lm32-firmware"
	@echo " make clean"
	@echo ""
	@echo "Environment:"
	@echo "  BOARD=atlys OR opsis  (current: $(BOARD))"
	@echo " TARGET=base OR hdmi2usb OR hdmi2ethernet"
	@echo "                        (current: $(TARGET)"
	@echo " MSCDIR=misoc directory (current: $(MSCDIR))"
	@echo "   PROG=programmer      (current: $(PROG))"
	@echo " SERIAL=serial port     (current: $(SERIAL))"

gateware: lm32-firmware
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv clean
	cp hdl/encoder/vhdl/header.hex $(MSCDIR)/build/header.hex
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream

load-gateware:
	cd $(MSCDIR) && $(CMD) load-bitstream

lm32-firmware:
	cd $(MSCDIR) && $(CMD) build-headers
	$(MAKE) -C firmware/lm32 all

load-lm32-firmware: lm32-firmware
	$(FLTERM) --port $(SERIAL) --kernel=firmware/lm32/firmware.bin --kernel-adr=0x20000000 --speed 115200

fx2-firmware:
	$(MAKE) -C firmware/fx2

load-fx2-firmware: fx2-firmware
	firmware/fx2/download.sh firmware/fx2/hdmi2usb.hex

clean:
	$(MAKE) -C firmware/lm32 clean
	$(MAKE) -C firmware/fx2 clean

all: gateware load-gateware load-lm32-firmware

.PHONY: lm32-firmware load clean
