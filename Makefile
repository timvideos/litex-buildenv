export CLANG=0

PLATFORM ?= opsis
export PLATFORM
# Default board
ifeq ($(PLATFORM),)
    $(error "PLATFORM not set, please set it.")
endif

TARGET ?= hdmi2usb
export TARGET

CPU ?= lm32
export CPU


TARGET_BUILD_DIR = build/$(PLATFORM)_$(TARGET)_$(CPU)/

IPRANGE ?= 192.168.100
TFTPD_DIR ?= build/tftpd/

# Couple of Python settings.
# ---------------------------------
# Turn off Python's hash randomization
PYTHONHASHSEED := 0
export PYTHONHASHSEED
# ---------------------------------

MAKE_CMD=\
	 ./make.py \
		--platform=$(PLATFORM) \
		--target=$(TARGET) \
		--cpu-type=$(CPU) \
		--iprange=$(IPRANGE) \
		$(MISOC_EXTRA_CMDLINE) \
		$(LITEX_EXTRA_CMDLINE) \

# We use the special PIPESTATUS which is bash only below.
SHELL := /bin/bash

FILTER ?= tee -a
LOGFILE ?= $(PWD)/$(TARGET_BUILD_DIR)/output.$(shell date +%Y%m%d-%H%M%S).log

# Initialize submodules automatically
third_party/%/.git: .gitmodules
	git submodule sync --recursive -- $$(dirname $@)
	git submodule update --recursive --init $$(dirname $@)
	touch $@ -r .gitmodules

# Gateware
MODULES=litex litedram liteeth litejpeg litepcie litesata litescope liteusb litevideo litex
gateware-submodules: $(addsuffix /.git,$(addprefix third_party/,$(MODULES)))
	@true

gateware: gateware-submodules
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) \
	| $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD)
endif

gateware-clean:
	rm -rf $(TARGET_BUILD_DIR)/gateware

firmware:
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) --no-compile-gateware \
	| $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD) --no-compile-gateware
endif

firmware-clean:
	rm -rf $(TARGET_BUILD_DIR)/software

load-gateware: load-gateware-$(PLATFORM)
	true

load-firmware: firmware load-firmware-$(PLATFORM)
	true

# Include platform specific targets
include targets/$(PLATFORM)/Makefile.mk

# TFTP server for minisoc to load firmware from
tftp: firmware
	mkdir -p $(TFTPD_DIR)
	cp $(TARGET_BUILD_DIR)/software/firmware/firmware.bin $(TFTPD_DIR)/boot.bin

tftpd_stop:
	sudo true
	sudo killall atftpd || true	# FIXME: This is dangerous...

tftpd_start:
	mkdir -p $(TFTPD_DIR)
	sudo true
	sudo atftpd --verbose --bind-address $(IPRANGE).100 --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) $(TFTPD_DIR) &

# Helper targets
help:
	echo "Hello"

clean:
	rm -rf $(TARGET_BUILD_DIR)
	py3clean . || rm -rf $$(find -name __pycache__)

dist-clean:
	rm -rf build

.PHONY: gateware firmware help clean dist-clean
