PYTHON = python3

firmware:
	$(MAKE) -C firmware all

load:
	$(PYTHON) tools/flterm.py --port 5 --kernel=firmware/firmware.bin

clean:
	$(MAKE) -C firmware clean

.PHONY: firmware load clean
