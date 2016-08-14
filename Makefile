CPU ?= lm32

opsis_base:
	rm -rf build
	./opsis_base.py --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./opsis_base.py --cpu-type $(CPU)

opsis_minisoc:
	rm -rf build
	./opsis_base.py --with-ethernet --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./opsis_base.py --with-ethernet --cpu-type $(CPU)

opsis_video:
	rm -rf build
	./opsis_video.py --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./opsis_video.py --cpu-type $(CPU)

opsis_hdmi2usb:
	rm -rf build
	./opsis_hdmi2usb.py --nocompile-gateware --cpu-type $(CPU)
	cd firmware && make clean all
	./opsis_hdmi2usb.py --cpu-type $(CPU)

opsis_sim:
	rm -rf build
	./opsis_sim.py --nocompile-gateware --with-ethernet --cpu-type $(CPU)
	cd firmware && make clean all
	./opsis_sim.py --with-ethernet --cpu-type $(CPU)

load:
	./load.py

firmware:
	cd firmware && make clean all

load-firmware:
	litex_term --kernel firmware/firmware.bin COM8

clean:
	rm -rf build

.PHONY: load firmware load-firmware
