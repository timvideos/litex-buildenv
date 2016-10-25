CPU ?= lm32
export CLANG=0

opsis_base:
	rm -rf build/opsis_base
	./opsis_base.py --cpu-type $(CPU)

opsis_minisoc:
	rm -rf build/opsis_minisoc
# FIXME
	mkdir -p build/opsis_minisoc/software/uip
	cp -r firmware/uip/* build/opsis_minisoc/software/uip
	mkdir -p build/opsis_minisoc/software/libuip
	cp -r firmware/libuip/* build/opsis_minisoc/software/libuip
# FIXME
	./opsis_base.py --with-ethernet --cpu-type $(CPU)

opsis_video:
	rm -rf build/opsis_video
# FIXME
	mkdir -p build/opsis_video/software/uip
	cp -r firmware/uip/* build/opsis_video/software/uip
	mkdir -p build/opsis_video/software/libuip
	cp -r firmware/libuip/* build/opsis_video/software/libuip
# FIXME
	./opsis_video.py --cpu-type $(CPU)

opsis_hdmi2usb:
	rm -rf build/opsis_hdmi2usb
# FIXME
	mkdir -p build/opsis_hdmi2usb/software/uip
	cp -r firmware/uip/* build/opsis_hdmi2usb/software/uip
	mkdir -p build/opsis_hdmi2usb/software/libuip
	cp -r firmware/libuip/* build/opsis_hdmi2usb/software/libuip
# FIXME
	./opsis_hdmi2usb.py --cpu-type $(CPU)

opsis_sim_setup:
	sudo openvpn --mktun --dev tap0
	sudo ifconfig tap0 192.168.1.100 up
	sudo mknod /dev/net/tap0 c 10 200
	sudo chown $(shell whoami) /dev/net/tap0
	sudo atftpd --bind-address 192.168.1.100 --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) build/opsis_sim/software/ &

opsis_sim_teardown:
	sudo killall atftpd || true	# FIXME: This is dangerous...
	sudo rm -f /dev/net/tap0
	sudo ifconfig tap0 down
	sudo openvpn --rmtun --dev tap0

opsis_sim:
	rm -rf build/opsis_sim
	./opsis_sim.py --with-ethernet --cpu-type $(CPU)

reset:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

load:
	opsis-mode-switch --verbose --load-gateware build/$(TARGET)/gateware/top.bit
	opsis-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/opsis0/tty --kernel=build/$(TARGET)/software/boot.bin

clean:
	rm -rf build

.PHONY: load firmware load-firmware
