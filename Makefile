MSCDIR ?= ../misoc
PROG ?= impact
SERIAL ?= /dev/ttyVIZ0

HDMI2USBDIR = $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHON = python3
SOC = VideostreamerSoC
LOWER_SOC  = $(shell tr '[:upper:]' '[:lower:]' <<< $(SOC))

CMD = $(PYTHON) make.py -X $(HDMI2USBDIR) -t atlys -s $(SOC) -Op programmer $(PROG)

gateware:
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv build-bitstream

load_gateware:
	cd $(MSCDIR) && $(CMD) load-bitstream

firmware:
	$(MAKE) -C firmware all

load_firmware: firmware
	$(PYTHON) tools/flterm.py --port $(SERIAL) --kernel=firmware/firmware.bin

load_firmware_alt: firmware
	$(MSCDIR)/tools/flterm --port $(SERIAL) --kernel=firmware/firmware.bin --kernel-adr=0x20000000

clean:
	$(MAKE) -C firmware clean

.PHONY: firmware load clean
