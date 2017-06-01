CPU ?= lm32

minisoc:
	rm -rf build
	./nexys_base.py --with-ethernet --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./nexys_base.py --with-ethernet --cpu-type $(CPU)

ddr3:
	rm -rf build
	./nexys_ddr3.py

etherbone:
	rm -rf build
	./nexys_etherbone.py --cpu-type $(CPU)

video:
	rm -rf build
	./nexys_video.py --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./nexys_video.py --cpu-type $(CPU)

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin COM5

.PHONY: load firmware load-firmware
