MSCDIR ?= ../misoc
PROG ?= impact
SERIAL ?= /dev/ttyVIZ0

HDMI2USBDIR = $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHON = python3
SOC = VideostreamerUSBSoC
LOWER_SOC  = $(shell tr '[:upper:]' '[:lower:]' <<< $(SOC))

CMD = $(PYTHON) make.py -X $(HDMI2USBDIR) -t atlys -s $(SOC) -Op programmer $(PROG)

ifeq ($(OS),Windows_NT)
	FLTERM = $(PYTHON) $(MSCDIR)/tools/flterm.py
else
	FLTERM = $(MSCDIR)/tools/flterm
endif

help:
	@echo "Targets avaliable:"
	@echo " make gateware"
	@echo " make load_gateware"
	@echo " make load_firmware (OR) make load_firmware_alt"
	@echo " make clean"
	@echo ""
	@echo "Environment:"
	@echo " MSCDIR=misoc directory (current: $(MSCDIR))"
	@echo "   PROG=programmer      (current: $(PROG))"
	@echo " SERIAL=serial port     (current: $(SERIAL))"
gateware:
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv clean
	cp hdl/encoder/vhdl/header.hex $(MSCDIR)/build/header.hex
	cp hdl/stream/vhdl/*.ngc $(MSCDIR)/build/
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream load-bitstream

load_gateware:
	cd $(MSCDIR) && $(CMD) load-bitstream

firmware:
	$(MAKE) -C firmware all

load_firmware: firmware
	$(FLTERM) --port $(SERIAL) --kernel=firmware/firmware.bin --kernel-adr=0x20000000 --speed 115200

clean:
	$(MAKE) -C firmware clean

all: gateware load_gateware load_firmware

.PHONY: firmware load clean
