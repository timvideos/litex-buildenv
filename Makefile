MSCDIR = ../misoc
HDMI2USBDIR = ../hdmi2usb
PYTHON = python3
SOC = VideostreamerSoC
LOWER_SOC  = $(shell tr '[:upper:]' '[:lower:]' <<< $(SOC))

CMD = $(PYTHON) make.py -X $(HDMI2USBDIR) -t atlys -s $(SOC) -Op programmer impact

gateware:
	cd $(MSCDIR) && $(CMD) --csr_csv $(HDMI2USBDIR)/test/csr.csv build-csr-csv all load-bitstream

load_gateware:
	cd $(MSCDIR) && $(CMD) load-bitstream

firmware:
	$(MAKE) -C firmware all

load_firmware:
	$(PYTHON) tools/flterm.py --port 5 --kernel=firmware/firmware.bin

clean:
	$(MAKE) -C firmware clean

.PHONY: firmware load clean
