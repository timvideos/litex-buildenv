CPU ?= lm32

nexys_minisoc:
	rm -rf build
	./nexys_base.py --with-ethernet --cpu-type $(CPU)

nexys_etherbone:
	rm -rf build
	./nexys_etherbone.py --cpu-type $(CPU)
load:
	./load.py
.PHONY: load firmware load-firmware
