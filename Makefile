opsis_minisoc:
	rm -rf build
	./opsis_base.py --with-ethernet --nocompile-gateware
	cd firmware && make clean all
	./opsis_base.py --with-ethernet

opsis_video:
	rm -rf build
	./opsis_video.py --nocompile-gateware
	cd firmware && make clean all
	./opsis_video.py

opsis_hdmi2usb:
	rm -rf build
	./opsis_hdmi2usb.py --nocompile-gateware
	cd firmware && make clean all
	./opsis_hdmi2usb.py

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin --kernel-adr 0x20000000 COM8

.PHONY: load firmware load-firmware
