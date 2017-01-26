netv2_base:
	rm -rf build
	./netv2_base.py

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin COM8

.PHONY: load firmware load-firmware
