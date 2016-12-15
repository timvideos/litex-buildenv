export CLANG=0

CPU ?= lm32
PLATFORM ?= opsis
TARGET ?= HDMI2USB

BUILD_DIR = build/$(PLATFORM)_$(shell echo $(TARGET) | tr '[:upper:]' '[:lower:]')_$(CPU)/

IPRANGE ?= 192.168.100
TFTPD_DIR ?= build/tftpd/

gateware:
	./make.py --platform=$(PLATFORM) --target=$(TARGET) --cpu-type=$(CPU) --iprange=$(IPRANGE)

firmware:
	./make.py --platform=$(PLATFORM) --target=$(TARGET) --cpu-type=$(CPU) --iprange=$(IPRANGE) --no-compile-gateware

load-gateware: load-gateware-$(PLATFORM)
	true

load-firmware: firmware load-firmware-$(PLATFORM)
	true

# opsis loading
load-gateware-opsis:
	opsis-mode-switch --verbose --load-gateware $(BUILD_DIR)/gateware/top.bit
	make TARGET=$(TARGET) load-firmware

load-firmware-opsis:
	opsis-mode-switch --verbose --mode=serial
	flterm --port=/dev/hdmi2usb/by-num/opsis0/tty --kernel=$(BUILD_DIR)/software/boot.bin

# minispartan6 loading
load-gateware-minispartan6:
	openocd -f board/minispartan6.cfg -c "init; pld load 0 $(BUILD_DIR)/gateware/top.bit; exit"

load-firmware-minispartan6:
	flterm --port=/dev/ttyUSB1 --kernel=$(BUILD_DIR)/software/boot.bin


# Sim targets
sim-setup:
	sudo openvpn --mktun --dev tap0
	sudo ifconfig tap0 $(IPRANGE).100 up
	sudo mknod /dev/net/tap0 c 10 200
	sudo chown $(shell whoami) /dev/net/tap0
	make TARGET=opsis_sim tftpd_start

sim-teardown:
	sudo killall atftpd || true	# FIXME: This is dangerous...

# TFTP server for minisoc to load firmware from
tftp: firmware
	mkdir -p $(TFTPD_DIR)
	cp build/$(PLATFORM)_$(TARGET)/software/boot.bin $(TFTPD_DIR)/boot.bin

tftpd_stop:
	sudo killall atftpd || true	# FIXME: This is dangerous...

tftpd_start:
	mkdir -p $(TFTPD_DIR)
	sudo atftpd --bind-address $(IPRANGE).100 --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) $(TFTPD_DIR) &

# Opsis specific targets
opsis-reset:
	opsis-mode-switch --verbose --mode=serial
	opsis-mode-switch --verbose --mode=jtag
	opsis-mode-switch --verbose --mode=serial

# Helper targets
clean:
	rm -rf build

all:
	PLATFORM=opsis; for TARGET in Base Net Video HDMI2USB; do \
		make PLATFORM=$(PLATFORM) TARGET=$$TARGET firmware; \
	done
	PLATFORM=minispartan6; for TARGET in Base; do \
		make PLATFORM=$(PLATFORM) TARGET=$$TARGET firmware; \
	done

.PHONY: gateware firmware opsis-reset load-gateware load-firmware
