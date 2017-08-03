ifneq ($(OS),Windows_NT)
ifeq ($(HDMI2USB_ENV),)
    $(error "Please enter environment. 'source scripts/enter-env.sh'")
endif
endif

PYTHON ?= python
export PYTHON

PLATFORM ?= opsis
export PLATFORM
# Default board
ifeq ($(PLATFORM),)
    $(error "PLATFORM not set, please set it.")
endif

# Include platform specific targets
include targets/$(PLATFORM)/Makefile.mk
ifeq ($(TARGET),)
    $(error "Internal error: TARGET not set.")
endif
export TARGET

ifeq ($(CPU),)
    $(error "Internal error: CPU not set.")
endif
export CPU

# We don't use CLANG
CLANG = 0
export CLANG

ifeq ($(TOFE_BOARD),)
FULL_PLATFORM = $(PLATFORM)
else
FULL_PLATFORM = $(PLATFORM).$(TOFE_BOARD)
LITEX_EXTRA_CMDLINE += -Ot tofe_board $(TOFE_BOARD)
endif
TARGET_BUILD_DIR = build/$(FULL_PLATFORM)_$(TARGET)_$(CPU)/

IPRANGE ?= 192.168.100
export IPRANGE
TFTPD_DIR ?= build/tftpd/

# Couple of Python settings.
# ---------------------------------
# Turn off Python's hash randomization
PYTHONHASHSEED := 0
export PYTHONHASHSEED
# ---------------------------------

MAKE_CMD=\
	time $(PYTHON) -u ./make.py \
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

# Image - a combination of multiple parts (gateware+bios+firmware+more?)
# --------------------------------------
image:
	$(PYTHON) mkimage.py $(MISOC_EXTRA_CMDLINE) $(LITEX_EXTRA_CMDLINE)

image-load: image image-load-$(PLATFORM)
	@true

image-flash: image image-flash-$(PLATFORM)
	@true

.PHONY: image image-load image-flash

# Gateware - the stuff which configures the FPGA.
# --------------------------------------
GATEWARE_MODULES=litex litedram liteeth litepcie litesata litescope liteusb litevideo litex
gateware-submodules: $(addsuffix /.git,$(addprefix third_party/,$(GATEWARE_MODULES)))
	@true

gateware: gateware-submodules
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) \
	2>&1 | $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD)
endif

gateware-load: gateware-load-$(PLATFORM)
	@true

gateware-flash: gateware-flash-$(PLATFORM)
	@true

gateware-clean:
	rm -rf $(TARGET_BUILD_DIR)/gateware

.PHONY: gateware gateware-load gateware-flash gateware-clean

# Firmware - the stuff which runs in the soft CPU inside the FPGA.
# --------------------------------------
firmware:
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) --no-compile-gateware \
	2>&1 | $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD) --no-compile-gateware
endif

firmware-load: firmware firmware-load-$(PLATFORM)
	@true

firmware-flash: firmware firmware-flash-$(PLATFORM)
	@true

firmware-connect: firmware-connect-$(PLATFORM)
	@true

firmware-clean:
	rm -rf $(TARGET_BUILD_DIR)/software

.PHONY: firmware firmware-load firmware-flash firmware-connect firmware-clean

# TFTP booting stuff
# --------------------------------------
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

.PHONY: tftp tftpd_stop tftpd_start

# Extra targets
# --------------------------------------
flash: image-flash
	@true

help:
	@echo "Environment:"
	@echo " PLATFORM=$(shell ls targets/ | grep -v ".py" | grep -v "common" | sed -e"s+targets/++" -e's/$$/ OR/')" | sed -e's/ OR$$//'
	@echo "                        (current: $(PLATFORM))"
	@echo " TARGET=$(shell ls targets/$(PLATFORM)/ | grep ".py" | grep -v "__" | sed -e"s+targets/$(PLATFORM)/++" -e's/.py/ OR/')" | sed -e's/ OR$$//'
	@echo "                        (current: $(TARGET))"
	@echo ""
	@if [ ! -z "$(TARGETS)" ]; then echo " Extra firmware needed for: $(TARGETS)"; echo ""; fi
	@echo "Targets avaliable:"
	@echo " make help"
	@echo " make all"
	@echo " make gateware"
	@echo " make firmware"
	@echo " make flash"
	@for T in $(TARGETS); do make -s help-$$T; done
	@echo " make clean"

clean:
	rm -rf $(TARGET_BUILD_DIR)
	py3clean . || rm -rf $$(find -name __pycache__)

dist-clean:
	rm -rf build

.PHONY: flash help clean dist-clean

# Tests
# --------------------------------------
TEST_MODULES=edid-decode
test-submodules: $(addsuffix /.git,$(addprefix third_party/,$(TEST_MODULES)))
	@true

test-edid: test-submodules
	$(MAKE) -C test/edid check

test:
	true

.PHONY: test test-edid
