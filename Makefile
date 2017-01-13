CPU ?= lm32

arty_base:
	rm -rf build
	./arty_base.py --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./arty_base.py --cpu-type $(CPU)

arty_minisoc:
	rm -rf build
	./arty_base.py --with-ethernet --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./arty_base.py --with-ethernet --cpu-type $(CPU)

arty_etherbone:
	rm -rf build
	./arty_etherbone.py

arty_ddr3:
	rm -rf build
	./arty_ddr3.py

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin --kernel-adr 0x20000000 /dev/ttyUSB1

.PHONY: load firmware load-firmware
