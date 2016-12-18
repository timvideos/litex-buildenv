export CLANG=0

CPU ?= lm32
export CPU
PLATFORM ?= opsis
export PLATFORM
TARGET ?= hdmi2usb
export TARGET

BUILD_DIR = build/$(PLATFORM)_$(TARGET)_$(CPU)/

IPRANGE ?= 192.168.100
TFTPD_DIR ?= build/tftpd/

help:
	echo "Hello"

gateware:
	./make.py --platform=$(PLATFORM) --target=$(TARGET) --cpu-type=$(CPU) --iprange=$(IPRANGE)

firmware:
	./make.py --platform=$(PLATFORM) --target=$(TARGET) --cpu-type=$(CPU) --iprange=$(IPRANGE) --no-compile-gateware

load-gateware: load-gateware-$(PLATFORM)
	true

load-firmware: firmware load-firmware-$(PLATFORM)
	true

# mimasv2 loading
load-gateware-mimasv2:
	MimasV2Config.py /dev/ttyACM0 $(BUILD_DIR)/gateware/top.bin

load-firmware-mimasv2:
	flterm --port=/dev/ttyACM0 --kernel=$(BUILD_DIR)/software/firmware/firmware.bin

# opsis loading
load-gateware-opsis: tftp
	opsis-mode-switch --verbose --load-gateware $(BUILD_DIR)/gateware/top.bit

load-firmware-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/opsis0/tty --kernel=$(BUILD_DIR)/software/firmware/firmware.bin

# minispartan6 loading
load-gateware-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(BUILD_DIR)/gateware/top.bit; exit"

load-firmware-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(BUILD_DIR)/software/firmware/firmware.bin


# Sim targets
sim-setup:
	sudo true
	sudo openvpn --mktun --dev tap0
	sudo ifconfig tap0 $(IPRANGE).100 up
	sudo mknod /dev/net/tap0 c 10 200
	sudo chown $(shell whoami) /dev/net/tap0
	make tftpd_start

sim-teardown:
	sudo true
	make tftpd_stop
	sudo rm -f /dev/net/tap0
	sudo ifconfig tap0 down
	sudo openvpn --rmtun --dev tap0

# TFTP server for minisoc to load firmware from
tftp: firmware
	mkdir -p $(TFTPD_DIR)
	cp $(BUILD_DIR)/software/firmware/firmware.bin $(TFTPD_DIR)/boot.bin

tftpd_stop:
	sudo true
	sudo killall atftpd || true	# FIXME: This is dangerous...

tftpd_start:
	mkdir -p $(TFTPD_DIR)
	sudo true
	sudo atftpd --verbose --bind-address $(IPRANGE).100 --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) $(TFTPD_DIR) &

# Opsis specific targets
opsis-reset:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

# Helper targets
clean:
	rm -rf build

all:
	PLATFORM=opsis; for TARGET in base net video hdmi2usb; do \
		make PLATFORM=$(PLATFORM) TARGET=$$TARGET firmware; \
	done
	PLATFORM=minispartan6; for TARGET in base; do \
		make PLATFORM=$(PLATFORM) TARGET=$$TARGET firmware; \
	done

.PHONY: gateware firmware opsis-reset load-gateware load-firmware
