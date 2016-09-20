CPU ?= lm32
export CLANG=0

opsis_base:
	rm -rf build/opsis_base
	./opsis_base.py --cpu-type $(CPU)

opsis_minisoc:
	rm -rf build/opsis_minisoc
	./opsis_base.py --with-ethernet --cpu-type $(CPU)

opsis_video:
	rm -rf build/opsis_video
	./opsis_video.py --cpu-type $(CPU)

opsis_hdmi2usb:
	rm -rf build/opsis_hdmi2usb
	./opsis_hdmi2usb.py --cpu-type $(CPU)

opsis_sim:
	rm -rf build/opsis_sim
	./opsis_sim.py --with-ethernet --cpu-type $(CPU)

load:
	./load.py

clean:
	rm -rf build

.PHONY: load firmware load-firmware
