MSCDIR = ../misoc
ARTYDIR = ../arty-soc
PYTHON = python3
TARGET = arty_base

CMD = $(PYTHON) make.py -X $(ARTYDIR) -t $(TARGET) --csr_csv $(ARTYDIR)/software/csr.csv

gateware:
	cd $(MSCDIR) && $(CMD) build-csr-csv build-bitstream

load:
	cd $(MSCDIR) && $(CMD) load-bitstream

clean:
	rm -f software/csr.csv

.PHONY: gateware load clean