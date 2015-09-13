BOARD ?= atlys
MSCDIR ?= build/misoc
PROG ?= impact
SERIAL ?= /dev/ttyVIZ0
TARGET ?= hdmi2usb

HDMI2USBDIR = ../..
PYTHON = python3
DATE = `date +%Y_%m_%d`

CMD = $(PYTHON) \
  make.py \
  -X $(HDMI2USBDIR) \
  -t $(BOARD)_$(TARGET) \
  -Ot firmware_filename $(HDMI2USBDIR)/firmware/lm32/firmware.bin \
  -Op programmer $(PROG) \
  $(MISOC_EXTRA_CMDLINE)

ifeq ($(OS),Windows_NT)
	FLTERM = $(PYTHON) $(MSCDIR)/tools/flterm.py
else
	FLTERM = $(MSCDIR)/tools/flterm
endif

include Makefile.$(TARGET)

help:
	@echo "Environment:"
	@echo "  BOARD=atlys OR opsis  (current: $(BOARD))"
	@echo " TARGET=base OR hdmi2usb OR hdmi2ethernet"
	@echo "                        (current: $(TARGET))"
	@echo "   PROG=programmer      (current: $(PROG))"
	@echo " SERIAL=serial port     (current: $(SERIAL))"
	@echo ""
	@echo "Targets avaliable:"
	@echo " make help"
	@echo " make gateware"
	@echo " make load-gateware"
	@echo " make connect-lm32"
	@make -s help-$(TARGET)
	@echo " make clean"
	@echo " make all"

clean: clean-$(TARGET)
	cd $(MSCDIR) && $(CMD) clean

load: load-gateware load-$(TARGET)

# Gateware targets
gateware: gateware-$(TARGET)
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv clean
	cp hdl/encoder/vhdl/header.hex $(MSCDIR)/build/header.hex
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream

load-gateware:
	cd $(MSCDIR) && $(CMD) load-bitstream

release-gateware:
	cd $(MSCDIR)/build && tar -cvzf ../$(HDMI2USBDIR)/$(BOARD)_$(TARGET)_gateware_$(DATE).tar.gz *.bin *.bit

# Firmware targets
firmware: firmware-$(TARGET)
	@true

connect-lm32:
	$(FLTERM) --port $(SERIAL) --speed 115200

# All target
all: gateware load-gateware load-$(TARGET)

.PHONY: help clean load gateware load-gateware release-gateware connect-lm32 all
