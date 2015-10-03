
ifneq ($(OS),Windows_NT)
ifneq "$(HDMI2USB_ENV)" "1"
$(error "Please 'source scripts/setup-env.sh'")
endif
endif

BOARD ?= atlys
MSCDIR ?= build/misoc
PROG ?= impact
SERIAL ?= /dev/ttyVIZ0
TARGET ?= hdmi2usb
FILTER ?= tee

HDMI2USBDIR = ../..
PYTHON = python3
DATE = `date +%Y_%m_%d`

# We use the special PIPESTATUS which is bash only below.
SHELL := /bin/bash

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

include Makefile.$(TARGET)

clean:
	make -s clean-$(TARGET)
	if [ -f $(MSCDIR)/software/include/generated/cpu.mak ]; then \
		(cd $(MSCDIR) && $(CMD) clean) \
	fi
	# FIXME - This is a temporarily hack until misoc clean works better.
	rm -rf $(MSCDIR)/software/include/generated && ( \
		mkdir $(MSCDIR)/software/include/generated && \
		touch $(MSCDIR)/software/include/generated/.keep_me)

load: load-gateware load-$(TARGET)

# Gateware targets
gateware:
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv clean
	cp hdl/encoder/vhdl/header.hex $(MSCDIR)/build/header.hex
ifneq ($(OS),Windows_NT)
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream \
	| $(FILTER) $(PWD)/build/output.$(DATE).log; (exit $${PIPESTATUS[0]})
else
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream
endif

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
