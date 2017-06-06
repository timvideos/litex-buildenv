base:
	rm -rf build
	./netv2_base.py

pcie:
	rm -rf build
	./netv2_pcie.py

video:
	rm -rf build
	./netv2_video.py

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin COM8

.PHONY: load firmware load-firmware
